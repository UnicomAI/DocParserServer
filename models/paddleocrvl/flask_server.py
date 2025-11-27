from pathlib import Path
from paddleocr import PaddleOCRVL
import time
from flask import Flask, request, jsonify
import uuid
import os
import base64
import io
import sys
config_dir = "/app/DocParserServer-main"
if config_dir not in sys.path:
    sys.path.append(config_dir)
from config import config
from utils.log_utils import setup_logger
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
pipeline = PaddleOCRVL(vl_rec_backend="vllm-server", vl_rec_server_url=config.model_address) # "http://127.0.0.1:8118/v1"

@app.route("/file_parse", methods=["POST"])
def pdf_to_markdown():
    try:
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
        output = pipeline.predict(input=str(upload_file_path))
        end_time = time.time()
        predict_cost = round(end_time - start_time, 2)
        logger.info(f"finished call vllm server: {upload_file_path}, cost: {predict_cost}s")
        # 8. 处理结果
        markdown_list = []
        markdown_images = []
        for res in output:
            md_info = res.markdown
            markdown_list.append(md_info)
            markdown_images.append(md_info.get("markdown_images", {}))

        # 9. 拼接 Markdown 文本
        markdown_texts = pipeline.concatenate_markdown_pages(markdown_list)

        # 10. 保存 Markdown 文件
        md_file_path = current_output_path / f"{file_stem}.md"
        md_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(md_file_path, "w", encoding="utf-8") as f:
            f.write(markdown_texts)

        # 11. 保存图片并收集绝对路径
        image_abs_paths = []
        images_base64 = {}
        for item in markdown_images:
            if item:
                for path, image in item.items():
                    img_file_path = current_output_path / path
                    img_file_path.parent.mkdir(parents=True, exist_ok=True)
                    image.save(img_file_path)
                    # 获取绝对路径
                    image_abs_paths.append(os.path.abspath(str(img_file_path)))

                    # 新增：将图片转为 Base64 编码（带数据头部，适配保存函数）
                    img_filename = Path(path).name  # 提取图片文件名（如 "img1.png"）
                    buffer = io.BytesIO()  # 内存缓冲区
                    image.save(buffer, format='jpeg')  # 按图片格式保存
                    buffer.seek(0)
                    base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")  # 编码为字符串
                    # 拼接 Base64 数据头部（保存函数会自动拆分）
                    images_base64[img_filename] = f"data:image/{img_filename.split('.')[-1]};base64,{base64_str}"
        # 12. 返回结果
        return jsonify({
            "code": 200,
            "message": "转换成功",
            "data": {
                "predict_time_cost": f"{predict_cost}秒",
                "md_content": markdown_texts,
                # "markdown_file_abs_path": os.path.abspath(str(md_file_path)),
                # "image_abs_paths": image_abs_paths,
                "images": images_base64
            }
        }),200,{'Content-Type': 'application/json; charset=utf-8'}

    except Exception as e:
        logger.error(f"转换失败：{e}", exc_info=True)
        return jsonify({
            "code": 500,
            "message": f"转换失败：{e}",
            "data": None
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)