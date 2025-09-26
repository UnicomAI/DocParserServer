# Yuanjing Wanwu Agent Platform - PDF Document Parsing Service

<div align="center">
  <img src="https://github.com/user-attachments/assets/6ceb4269-a861-4545-84db-bad322592156" style="width:45%; height:auto;" />

  <p>
    <a href="#features">Features</a> •
    <a href="#local-deployment">Local Deployment</a> •
    <a href="#data-protocol">Data Protocol</a> •
    <a href="#how-to-use">how to use</a> •
    <a href="#contact-us">Contact Us</a> 
  </p>

  <p>
    <img alt="License" src="https://img.shields.io/badge/license-apache2.0-blue.svg">
    <img alt="Python Version" src="https://img.shields.io/badge/python-%3E%3D%203.10-blue">
    <a href="https://github.com/UnicomAI/DocParserServer/releases">
      <img alt="Release Notes" src="https://img.shields.io/github/v/release/UnicomAI/DocParserServer?label=Release&logo=github&color=green">
    </a>
  </p>

  <p>
    English | <a href="https://github.com/UnicomAI/DocParserServer/blob/main/README.md">中文</a> 
  </p>
</div>

&emsp;&emsp;**Yuanjing Wanwu Agent Platform** ([GitHub Repository](https://github.com/UnicomAI/wanwu/edit/main/README_CN.md)) is an **enterprise-grade** one-stop **commercially license-friendly** agent development platform, dedicated to providing enterprises with secure, efficient, and compliant one-stop AI solutions. With the core philosophy of "technology openness and ecological co-construction", we have built a comprehensive AI engineering platform covering the entire model lifecycle management, MCP, internet retrieval, rapid agent development, enterprise knowledge base construction, complex workflow orchestration, and other functional systems by integrating cutting-edge technologies such as large language models and business process automation. The platform adopts a modular architecture design, supporting flexible function expansion and secondary development, while ensuring enterprise data security and privacy protection, significantly reducing the application threshold of AI technology. Whether it is small and medium-sized enterprises quickly building intelligent applications or large enterprises realizing intelligent transformation of complex business scenarios, Yuanjing Wanwu Agent Platform can provide strong technical support to help enterprises accelerate the digital transformation process, achieve cost reduction, efficiency improvement, and business innovation.

&emsp;&emsp;**Wanwu PDF Document Parsing Service** focuses on PDF document parsing. It can accurately convert PDFs to Markdown format and efficiently extract complex multimodal knowledge such as tables, formulas, and images from documents. With this service, the ability to understand and extract PDF content can be enhanced, thereby significantly improving the application effect of the Wanwu platform in knowledge-based scenarios such as RAG knowledge question answering and agent knowledge base nodes.

------


## Features

Supports PDF document parsing and output in standard markdown format, with high-quality parsing of complex multimodal knowledge such as title hierarchies, tables, formulas, and images.

Among them:
- Tables are converted to HTML format for output
- Formulas are output in LaTeX syntax format
- Images are output as Minio links

It also supports cloud trial and privatized deployment. For open-source deployment images, please refer to: [Local Deployment](#installation-via-image-recommended)


### Key Features of Document Parsing

- **Diversified Content Extraction**: Supports extraction of images, image descriptions, tables, table titles, and footnotes
  
- **Formula Conversion**: Automatically identifies formulas in documents and converts them to LaTeX format
  
- **Table Conversion**: Automatically identifies tables in documents and converts them to HTML format
  
- **OCR Function**: Automatically detects scanned PDFs and garbled PDFs, and enables OCR function
  
- **Multilingual Support**: OCR function supports detection and recognition of multiple languages
  
- **Standard Format**: Supports output in standard Markdown format, which is more friendly for large models to understand the format
  
- **Multiple Operating Environments**: Supports running in pure CPU environment, and supports GPU (CUDA)/NPU (adapting, coming soon) acceleration

## Local Deployment

### Installation via Image (Recommended)
```bash
# arm64
docker pull crpi-6pj79y7ddzdpexs8.cn-hangzhou.personal.cr.aliyuncs.com/wanwulite/doc_parser_server:1.1-20250925-arm64
# x86_64
docker pull crpi-6pj79y7ddzdpexs8.cn-hangzhou.personal.cr.aliyuncs.com/wanwulite/doc_parser_server:1.1-20250925-amd64

# check image is existed
docker images|grep doc_parser_server
# docker run start the container
# BFF_SERVICE_MINIO will be avaliable once deploying wanwu platform.
docker run -itd --name doc_parser \
-p 8083:8083 \
-e MINIO_ADDRESS="192.168.0.1:9000" \
-e MINIO_ACCESS_KEY="root" \
-e MINIO_SECRET_KEY="Minio_SK" \
-e BFF_SERVICE_MINIO="http://192.168.0.1:6668/v1/api/deploy/info" \
-e MINERU_ADDRESS="http://127.0.0.1:8000/file_parse" \
-e MINERU_MODEL_SOURCE=local \
-e DOC_PARSER_SERVER_PORT=8083 \
doc_parser_server:1.1 \
/app/start_all.sh
```

### Installation via Source Code
Pre-dependency preparation: python3.10.x, pip, miniconda, git, default port 8083Install document parsing service
bash
Clone the project to the local environment
```bash
git clone https://github.com/UnicomAI/DocParserServer.git
cd /path/to/DocParserServer
# Create a conda environment and install dependencies
conda create -n "wanwu_doc_parser_server" python=3.10
conda activate wanwu_doc_parser_server
pip install -r requirements.txt
# Start the service
bash start_app.sh
lsof -i:8083
# If you need to modify the default port number, you need to modify the environment variable and restart the document parsing service. Otherwise, no need to execute.
export DOC_PARSER_SERVER_PORT=your_port
bash start_app.sh
lsof -i:your_port
```
Install MinerU service: Refer to MinerU's official documentation.Test whether the service can run normally through the mineru command line
```bash
mineru -p <input_path> -o <output_path>
```
After it can run normally, start the MinerU service through fast api, the default port is 8000
```bash
cd /path/to/MinerU/mineru/cli
python fast_api.py
lsof -i:8000
# If you need to modify the default port number of the mineru fast api service, you also need to modify the environment variable and restart the document parsing service. Otherwise, no need to execute.
cd /path/to/DocParserServer
conda activate wanwu_doc_parser_server
export MINERU_ADDRESS="http://127.0.0.1:8000/file_parse"
bash start_app.sh
```

## Data Protocol
### Health Check Interface
#### Overview
Used to check if the service is started normally.
#### Request Method
`GET /rag/health`
#### Request Parameters
None
#### Response Example
```json
{
  "code": "200", 
  "status": "healthy", 
  "service": "doc_parser_server"
}
```
### Document Processing Interface
#### Overview
Process the uploaded document file, perform parsing and recognition tasks, and return the processing result.
#### Request Method
`POST /rag/model_parser_file`
#### Request Parameters
##### Request Header
- **Content-Type**: ` multipart/form-data`

##### Request Body (Form Data)

| 参数名         | 类型             | 必选 | 描述                                                           |
|----------------|----------------|----|--------------------------------------------------------------|
| `file_name`    | string         | T  | file name（ `file_name.pdf`）。                                 |
| `file`         | multipart file | T  | file stream（ PDF only）。                                      |
| `extract_image`| int            | F  | extract image：<br>0：do not extract <br>1：extract（by default） |


##### Response Example
Success Response (200 OK)
```json
{
    "code": "200",
    "content": "#sample content title \n ## content",
    "message": "Document processing completed",
    "status": "success",
    "trace_id": "060b05bb-8356-44a4-94a6-d4812670ddcc"
}
```
Error Response (400/500 failed)
```json
{
    "code": "400",
    "content": "",
    "message": "file_name is required",
    "status": "failed",
    "trace_id": "060b05bb-8356-44a4-94a6-d4812670ddcc"
}
```
#### Status Code Description

| 状态码 | 含义 |
|--------|------|
| 200    | Successfully processed the document and returned the result. |
| 400    | Request parameter error (e.g., no file uploaded, missing parameters, incorrect parameter format, etc.). |
| 500    | Internal service error (e.g., file processing failure, URL processing failure, model exception). |

## How to use
### Verification via curl Call
```bash
curl --location 'https:/{ip:127.0.0.1}:{port:8083}/rag/model_parser_file' \
--form 'file_name="demo.pdf"' \
--form 'file=@"/path/to/demo.pdf"'
```
Return as follows:
```bash
{
  "code": "200",
  "content": "2\n\n![Figure 1 Integrated Air System Control Cabinet Installation - Electrical Equipment (Total 4 pages, Page 1)](https://obs-nmhhht6.cucloud.cn/doc-rag-public/tmps34xnwa4.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=7123F0A077C64FDFA2DE87BAAF6D13363776%2F20250912%2Fcn-huhehaote-6%2Fs3%2Faws4_request&X-Amz-Date=20250912T091253Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host&X-Amz-Signature=40005a32ee961863c9a82f602a0dd01be4f2fdedb7e8d29daf137e9fd2e3e448) 220",
  "message": "Document processing completed",
  "status": "success",
  "trace_id": "df916082-072f-4019-a517-0ebb46077263"
}
```
### Calling via Python Code
```bash
def test_model_parser_file():
    file_path = r'/path/to/demo.pdf'
    file_name = 'demo.pdf'
    MODEL_PARSER_URL = 'http://{ip:127.0.0.1}:{port:8083}/rag/model_parser_file'

    files = {
        'file': (file_name, open(file_path, 'rb'), 'application/pdf')
    }

    data = {
        'file_name': file_name
    }

    try:
        response = requests.post(MODEL_PARSER_URL, files=files, data=data)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
```
## Contact Us
### DingTalk Q&A Group QR Code:
![DingTalk QR code](https://github.com/UnicomAI/DocParserServer/blob/main/文档解析答疑钉钉群二维码.png)
### DingTalk Q&A Group Link:
https://qr.dingtalk.com/action/joingroup?code=v1,k1,pBNnQOXRnlSdYb6nUM0RdzgmYNGkZuwjTFEJKG3JrHhuRVJIwrSsXmL8oFqU5ajJ&_dt_no_comment=1&origin=11? Invites you to join the DingTalk group chat "Wanwu Document Parsing Service Q&A Group", click to view details
