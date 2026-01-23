import os
import traceback
import uuid

from flask import Flask, request, jsonify
from flask_cors import CORS
from marshmallow import Schema, fields, ValidationError

from config import config
from models.ModelStrategy import CLIENT_STRATEGIES
from utils.file_utils import save_file_to_local
# 初始化日志
from utils.log_utils import setup_logger, set_trace_id, get_trace_id
from utils.monitor_utils import log_time

logger = setup_logger(__name__, './logs/app.log')

from utils.file_convert_utils import convert_to_pdf
client = CLIENT_STRATEGIES[config.model_type](config.model_address)

ALLOWED_FILE_EXTENSIONS = (".pdf", ".png", ".jpeg", ".jpg", ".webp", ".gif", ".docx", ".doc", ".ppt", "pptx")
MODEL_FILE_EXTENSIONS = (".pdf", ".png", ".jpeg", ".jpg", ".webp", ".gif")

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
                "message": f"请上传文件",
                "content": "",
                "trace_id": get_trace_id()
            }), 400
    if not file.filename.lower().endswith(ALLOWED_FILE_EXTENSIONS):
        return jsonify({
            "code": "400",
            "status": "failed",
            "message": "上传的文件类型错误",
            "content": "",
            "trace_id": get_trace_id()
        }), 400

    data = request.form.to_dict()

    logger.info(f"request data is: {data}")
    file_name = data.get('file_name', None)
    if not file_name.lower().endswith(ALLOWED_FILE_EXTENSIONS):
        return jsonify({
            "code": "400",
            "status": "failed",
            "message": "上传的文件扩展名错误",
            "content": "",
            "trace_id": get_trace_id()
        }), 400
    normalized_path = os.path.normpath(file_name)
    if normalized_path.startswith(('..', '/', '\\')):  # 防止跨目录访问
        return jsonify({
            "code": "400",
            "status": "failed",
            "message": "文件名包含非法字符: ..或/或\\",
            "content": "",
            "trace_id": get_trace_id()
        }), 400
    # 获取请求参数
    extract_image = data.get('extract_image', 'False').lower() == 'true'
    extract_image_content = int(data.get('extract_image_content', 0))
    return_json = data.get('return_json', 'False').lower() == 'true'
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
        # 转换为PDF
        file_path = convert_to_pdf(file_path)
        if not file_path.lower().endswith(MODEL_FILE_EXTENSIONS):
            return jsonify({
                "code": "500",
                "status": "failed",
                "message": f"File type is supported, but convert to model input(pdf/image) failed. Check file converter service. File_name: {file_name}",
                "content": "",
                "trace_id": get_trace_id()
            }), 500
        logger.info("start to parse file: %s", file_name)
        # 无模型mock返回测试
        # response = {
        #     "results": {
        #         "zc2023_P658": {
        #             "md_content": "# 元景-PDF文档解析测试文件\n\n欢迎使用万物智能体开发平台。![](test.png)。",
        #             "images": {}
        #         }
        #     }
        # }
        response = client.parse_file(file_path, return_json)
        logger.info(f"parse done! started to post process file: {file_path}")
        md_content,json_content = client.post_process(extract_image=extract_image,
                            extract_image_content=extract_image_content,
                            file_name=file_name,
                            file_path=file_path,
                            return_json=return_json,
                            response=response)
        logger.info(f"post process done! Finished. {file_path}")

        return jsonify({"code": "200","status": "success","message": "文档处理完成","content": md_content,"json_content":json_content,"trace_id": get_trace_id()})

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
            logger.error(f"删除文件失败,Trace ID: {get_trace_id()}, exception: {e}")

@app.route('/rag/test', methods=['GET'])
def test():
    return True



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.doc_parser_server_port, debug=True, use_reloader=False)
