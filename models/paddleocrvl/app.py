import json
from pathlib import Path
from paddleocr import PaddleOCRVL
import time
from flask import Flask, request, jsonify
import uuid
import os
import base64
import io
import sys


config_dir = "/app/DocParserServer"
if config_dir not in sys.path:
    sys.path.append(config_dir)
from config import config
logger_dir = "/app/DocParserServer/utils"
if logger_dir not in sys.path:
    sys.path.append(logger_dir)
from log_utils import setup_logger
from utils import merge_json_structure
# 初始化 Flask 应用
app = Flask(__name__)
logger = setup_logger(__name__, './flask_server.log')
# 配置参数
UPLOAD_FOLDER = "./uploads"  # 上传文件临时存储目录
OUTPUT_FOLDER = "./output"   # 处理结果输出目录

# 创建必要目录
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

# 初始化 PaddleOCRVL 实例（全局单例，避免重复初始化）
pipeline = PaddleOCRVL(vl_rec_backend="vllm-server",
                       vl_rec_server_url=config.model_address,
                       vl_rec_max_concurrency=32,
                       format_block_content=True) # "http://127.0.0.1:8118/v1"

@app.route("/file_parse", methods=["POST"])
def pdf_to_markdown():
    try:
        return_json = request.form.get('return_json', 'false').lower() == 'true'
        extract_image_content = request.form.get('extract_image_content', 'false').lower() in ('true', '1')
        # 1. 检查请求中是否包含文件
        if "file" not in request.files:
            return jsonify({
                "code": 400,
                "message": "请求中未包含文件",
                "data": None
            }), 400

        file = request.files["file"]

        # 2. 检查文件名是否合法
        if file.filename == "":
            return jsonify({
                "code": 400,
                "message": "文件名不能为空",
                "data": None
            }), 400


        # 4. 生成唯一文件名，避免冲突
        file_ext = file.filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        upload_file_path = Path(UPLOAD_FOLDER) / unique_filename

        # 5. 保存上传的文件
        file.save(upload_file_path)
        logger.info(f"start to call vllm server: {upload_file_path}")

        # 6. 初始化当前文件的输出目录（按唯一ID区分）
        file_stem = unique_filename.rsplit(".", 1)[0]
        current_output_path = Path(OUTPUT_FOLDER) / file_stem

        # 7. 执行 OCR 转换
        start_time = time.time()
        output = []
        for result in pipeline.predict_iter(input=str(upload_file_path),
                                             use_ocr_for_image_block=extract_image_content):
            output.append(result)
        end_time = time.time()
        predict_cost = round(end_time - start_time, 2)
        logger.info(f"finished call vllm server: {upload_file_path}, cost: {predict_cost}s")

        try:
            if upload_file_path.exists() and upload_file_path.is_file():  # 确保是文件且存在
                upload_file_path.unlink()  # 删除文件
        except Exception as e:
            # 仅记录错误，不中断后续流程
            app.logger.error(f"删除原始上传文件失败：{upload_file_path} | 错误信息：{str(e)}")

        res = pipeline.restructure_pages(res_list=output, merge_tables=True, relevel_titles= True, concatenate_pages= True)
        res[0].save_to_markdown(save_path=current_output_path)
        res[0].save_to_json(save_path=current_output_path)

        # 读取md文件（路径：current_output_path/file_stem.md）
        md_file = current_output_path / f"{file_stem}.md"
        with open(md_file, "r", encoding="utf-8") as f:
            markdown_texts = f.read()

        # 读取图片（路径：current_output_path/imgs）
        images_dict = {}
        imgs_dir = current_output_path / "imgs"
        if imgs_dir.exists():
            for img_path in sorted(imgs_dir.glob("*")):
                filename = img_path.name
                with open(img_path, "rb") as img_f:
                    base64_str = base64.b64encode(img_f.read()).decode("utf-8")
                    images_dict[filename] = f"data:image/{filename.split('.')[-1]};base64,{base64_str}"

        result_data = {
            "predict_time_cost": f"{predict_cost}秒",
            "md_content": markdown_texts,
            "images": images_dict
        }
        if return_json:
            try:
                json_file = current_output_path / f"{file_stem}_res.json"
                with open(json_file, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                result_data["json_data"] = json_data
            except Exception as e:
                app.logger.error(f"对{current_output_path}路径下的{file_stem}合并JSON结构失败：{e}", exc_info=True)
                result_data["json_data"] = None
        # 12. 返回结果
        return jsonify({
            "code": 200,
            "message": "转换成功",
            "data": result_data,
        }), 200

    except Exception as e:
        logger.error(f"转换失败：{e}", exc_info=True)
        return jsonify({
            "code": 500,
            "message": f"转换失败：{e}",
            "data": None
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)