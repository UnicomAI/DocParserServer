import os
import traceback
import uuid

from flask import Flask, request, jsonify
from flask_cors import CORS
from marshmallow import Schema, fields, ValidationError

from models.mineru.client import MineruClient
from utils.file_utils import save_file_to_local, extract_images_from_md, \
    save_images_res_to_local
from utils.monitor_utils import log_time


# 初始化日志
from utils.log_utils import setup_logger, set_trace_id, get_trace_id
logger = setup_logger(__name__, './logs/app.log')

MINIO_ADDRESS = os.getenv("MINERU_ADDRESS", "http://0.0.0.0:8000/file_parse")
client = MineruClient(MINIO_ADDRESS)

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

    logger.info(f"request data is: {data}")
    file_name = data.get('file_name', None)

    # 获取请求参数
    extract_image = data.get('extract_image', 1)
    file_path = ""
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
        # 无模型mock返回测试
        # response = {
        #     "results": {
        #         "zc2023_P658": {
        #             "md_content": "# 元景-PDF文档解析测试文件\n\n欢迎使用万物智能体开发平台。![](test.png)。",
        #             "images": {}
        #         }
        #     }
        # }
        results = response["results"][file_name.rsplit('.', 1)[0]]
        md_content = results.get('md_content')
        save_images_res_to_local(file_name, results)
        if extract_image and md_content:
            logger.info(f"extracting images for file: {file_path}")
            md_content = extract_images_from_md(md_content,"./data/images")

        return jsonify({"code": "200","status": "success","message": "文档处理完成","content": md_content,"trace_id": get_trace_id()})

    except Exception as e:
        # 获取当前的堆栈跟踪信息
        stack_trace = traceback.format_exc()
        # 获取 trace_id
        trace_id = get_trace_id()
        # 记录详细的错误信息，包括 trace_id 和堆栈跟踪
        logger.error(f"Error occurred. Trace ID: {trace_id}. Exception: {e}. Stack Trace: {stack_trace}")
        # 返回处理结果
        return jsonify({"code": "500",
            "status": "failed",
            "message": str(e),
            "content": "",
            "trace_id": get_trace_id()
        }), 500
    finally:
        # 删除存的原始文件
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"删除文件失败: {e}")

@app.route('/rag/test', methods=['GET'])
def test():
    return True



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083, debug=True, use_reloader=False)
