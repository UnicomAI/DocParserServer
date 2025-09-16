# import logging
import os
import traceback
import uuid

import yaml
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from marshmallow import Schema, fields, ValidationError

from models.dolphin.client import DolphinClient
from models.mineru.client import MineruClient
from utils.file_utils import save_file_to_local, save_file_url_to_local, extract_images_from_md, \
    save_images_res_to_local
from utils.monitor_utils import log_time


# from logging.handlers import RotatingFileHandler

# 加载配置文件
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
config = load_config()

# 初始化日志
from utils.log_utils import setup_logger, set_trace_id, get_trace_id

logger = setup_logger(__name__, './logs/app.log')

# 初始化文档解析模型client
model_name = config.get('default_model', 'mineru')
if model_name == 'mineru':
    client = MineruClient(config['models']['mineru']['base_url'])
elif model_name == 'dolphin':
    client = DolphinClient(config['models']['dolphin']['base_url'])
else:
    raise ValueError(f"Init exception. Unsupported model config: {model_name}")

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

@app.before_request
def before_request():
    # 生成唯一的 trace_id
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)

@app.route('/rag/health', methods=['GET'])
def health_check():
    logger.info("test log")
    """服务健康检查接口"""
    return jsonify({"code": "200", "status": "healthy", "service": "doc_parser_server"})

# class ModelParserSchema(Schema):
#     file_link = fields.Str(required=True)
#     file_name = fields.Str(required=True)
#     extract_image = fields.Int(required=False)
#     max_batch_size = fields.Int(required=False)
#
# @app.route('/rag/model_parser_url', methods=['POST'])
# @log_time
# def model_parser_url():
#     """文档处理API接口
#     接收文件上传和处理参数，返回处理结果
#     """
#     logger.info("test log")
#     # 参数校验
#     schema = ModelParserSchema()
#     try:
#         schema.load(request.get_json())
#     except ValidationError as err:
#         return jsonify(err.messages), 400
#
#     data = request.get_json()
#     logger.info(f"request data is:{data}")
#     file_link = data.get('file_link', None)
#     file_name = data.get('file_name', None)
#
#     # 获取请求参数
#     max_batch_size = 4
#     extract_image = data.get('extract_image', 1)
#
#     try:
#         # 保存文件到本地
#         file_path = save_file_url_to_local(file_link, file_name)
#         if not file_path:
#             return jsonify({
#                 "code": "500",
#                 "status": "failed",
#                 "message": f"File download failed. File_link: {file_link}, file_name: {file_name}",
#                 "content": "",
#                 "trace_id": get_trace_id()
#             }), 500
#         logger.info(f"File downloaded and saved to {file_path}")
#         # 根据配置调模型
#         # response = client.parse_file(file_path)
#         # logger.info(f"response is:{response}")
#         # md_content = response.get("123")
#
#         # if extract_image == 1 and md_content != "":
#         #     md_content = extract_images_from_md(md_content)
#         #     # 保存处理后的 Markdown 文件
#         #     base, extension = os.path.splitext("./data/123.md")
#         #     processed_md_path = f"{base}_processed{extension}"
#         #     with open(processed_md_path, "w", encoding="utf-8") as processed_md_file:
#         #         processed_md_file.write(md_content)
#         #     logger.info(f"Processed Markdown file saved to {processed_md_path}")
#         # 返回处理结果
#         return jsonify({
#             "code": "200",
#             "status": "success",
#             "message": "文档处理完成",
#             "content": "coming soon",
#             "trace_id": get_trace_id()
#         })
#
#     except Exception as e:
#         # 返回处理结果
#         return jsonify({
#             "code": "500",
#             "status": "failed",
#             "message": str(e),
#             "content": "",
#             "trace_id": get_trace_id()
#         }), 500


class ModelParserFileSchema(Schema):
    file_name = fields.Str(required=True, error_messages={"required": "file_name is required"})
    extract_image = fields.Int(required=False)
    max_batch_size = fields.Int(required=False)



@app.route('/rag/model_parser_file', methods=['POST'])
@log_time
def model_parser_file():
    """文档处理API接口
    接收文件上传和处理参数，返回处理结果
    """
    # 参数校验
    file = request.files.get('file')
    if not file:
        return jsonify({
                "code": "400",
                "status": "failed",
                "message": f"no file part",
                "content": "",
                "trace_id": get_trace_id()
            }), 400

    schema = ModelParserFileSchema()
    data = request.form.to_dict()
    try:
        schema.load(data)
    except ValidationError as err:
        error_messages = []
        for field, messages in err.messages.items():
            error_messages.extend(messages)
        return jsonify({
            "code": "400",
            "status": "failed",
            "message": "; ".join(error_messages),
            "content": "",
            "trace_id": get_trace_id()
        }), 400

    # data = request.get_json()
    logger.info(f"request data is: {data}")
    file_name = data.get('file_name', None)

    # 获取请求参数
    extract_image = data.get('extract_image', 1)
    file_path = ""
    parse_dir = ""
    try:
        # 保存文件到本地
        file_path = save_file_to_local(file, file_name)
        if not file_path:
            return jsonify({
                "code": "500",
                "status": "failed",
                "message": f"File save failed. file_name: {file_name}",
                "content": "",
                "trace_id": get_trace_id()
            }), 500
        logger.info(f"File downloaded and saved to {file_path}")
        # 根据配置调模型
        response = client.parse_file(file_path)
        results = response["results"][file_name.rsplit('.', 1)[0]]
        md_content = results.get('md_content')
        save_images_res_to_local(file_name, results)
        #返回图片链接目录，返回json文件
        if extract_image and md_content:
            logger.info(f"extracting images for file: {file_path}")
            # md_content = extract_images_from_md(md_content, os.path.join(os.path.dirname(os.path.abspath(__file__)),"data/images"))
            md_content = extract_images_from_md(md_content,"./data/images")
        # 返回处理结果
        return jsonify({
            "code": "200",
            "status": "success",
            "message": "文档处理完成",
            "content": md_content,
            "trace_id": get_trace_id()
        })

    except Exception as e:
        # 获取当前的堆栈跟踪信息
        stack_trace = traceback.format_exc()
        # 获取 trace_id
        trace_id = get_trace_id()
        # 记录详细的错误信息，包括 trace_id 和堆栈跟踪
        logger.error(f"Error occurred. Trace ID: {trace_id}. Exception: {e}. Stack Trace: {stack_trace}")
        # 返回处理结果
        return jsonify({
            "code": "500",
            "status": "failed",
            "message": str(e),
            "content": "",
            "trace_id": get_trace_id()
        }), 500
    finally:
        # 删除存的原始文件
        os.remove(file_path)

@app.route('/rag/test', methods=['GET'])
def test():
    file_path = r'./output.zip'
    if not os.path.isfile(file_path):
        logger.info(f"文件不存在：{file_path}")
        return "文件不存在", 404
    try:
        # 直接返回文件流
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.info(f"请求异常：{e}")
        return "请求异常", 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083, debug=True, use_reloader=False)
