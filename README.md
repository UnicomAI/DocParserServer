# DocParserServer 万悟文档解析服务


## 功能介绍
支持PDF文档解析并按markdown标准格式输出，支持标题层级、表格、公式、图片等复杂多模知识高质量解析，其中表格转换为HTML格式输出，公式以LaTeX语法格式输出，图片以oss链接输出。即支持云端试用也支持私有化部署，开源部署镜像参见：xxx
**文档解析方面具有以下关键特点：**
**多样化内容提取**：支持提取图像、图像描述、表格、表格标题和脚注。
**公式转换**自动识别文档中的公式并转换为LaTeX格式。
**表格转换**自动识别文档中的表格并转换为HTML格式。
**OCR功能**自动检测扫描版PDF和乱码PDF，并启用OCR功能。
**多语言支持**OCR功能支持多种语言的检测和识别。
**标准格式**：支持按Markdown标准格式输出，对大模型理解格式更友好。
**多种运行环境**支持纯CPU环境运行，并支持GPU(CUDA)/NPU(适配中敬请期待)加速。

## 本地部署
### 通过源码快速安装
```bash
git clone https://github.com/UnicomAI/DocParserServer.git
cd DocParserServer
# 建议python=3.10
pip install -r requirements.txt
bash start_app.sh
```
建议使用conda环境
```bash
conda create -n "doc_parser_server" python=3.10
conda activate doc_parser_server
```

### 通过镜像快速安装
```bash
TBD
```

### 安装依赖
安装mineru以及模型并且把mineru的地址配置到配置文件中 DocParserServer/config.yaml
参考链接：https://github.com/opendatalab/MinerU/blob/master/README_zh-CN.md 

## 使用服务
通过curl调用验证
```bash
curl --location 'https:/{ip:127.0.0.1}:{port:8083}/rag/model_parser_file' \
--form 'file_name="demo.pdf"' \
--form 'file=@"/home/demo/demo.pdf"'
```

返回如下：
```bash
{
  "code": "200",
  "content": "2\n\n![\u56fe1\u7efc\u5408\u7a7a\u6c14\u7cfb\u7edf\u63a7\u5236\u76d2\u5b89\u88c5 \uff0d\u7535\u5b50\u7535\u6c14\u8bbe\u5907\u67b6(\u51714\u5f20 \u7b2c1\u5f20)](https://obs-nmhhht6.cucloud.cn/doc-rag-public/tmps34xnwa4.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=7123F0A077C64FDFA2DE87BAAF6D13363776%2F20250912%2Fcn-huhehaote-6%2Fs3%2Faws4_request&X-Amz-Date=20250912T091253Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host&X-Amz-Signature=40005a32ee961863c9a82f602a0dd01be4f2fdedb7e8d29daf137e9fd2e3e448) 220",
  "message": "文档处理完成",
  "status": "success",
  "trace_id": "df916082-072f-4019-a517-0ebb46077263"
}
```
