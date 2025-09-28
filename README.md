# 元景万悟智能体平台-文档解析服务

<div align="center">
  <img src="https://github.com/user-attachments/assets/6ceb4269-a861-4545-84db-bad322592156" style="width:45%; height:auto;" />

  <p>
    <a href="#功能介绍">功能介绍</a> •
    <a href="#本地部署">本地部署</a> •
    <a href="#数据协议">数据协议</a> •
    <a href="#使用服务">使用服务</a> •
    <a href="#联系我们">联系我们</a> 
  </p>

  <p>
    <img alt="License: AGPL-3.0" src="https://img.shields.io/badge/license-AGPL--3.0-blue.svg">
    <img alt="Python Version" src="https://img.shields.io/badge/python-%3E%3D%203.10-blue">
    <a href="https://github.com/UnicomAI/DocParserServer/releases">
      <img alt="Release Notes" src="https://img.shields.io/github/v/release/UnicomAI/DocParserServer?label=Release&logo=github&color=green">
    </a>
  </p>

  <p>
    <a href="https://github.com/UnicomAI/DocParserServer/blob/main/README_EN.md">English</a> | 中文
  </p>
</div>


&emsp;&emsp;**万悟PDF文档解析服务**是一款面向**企业级**场景的通用文档解析服务，通过引入AI能力和多种业界领先的视觉文档解析模型，精准、高效的将各类文档转化为 Markdown 结构化标准格式，支持提取文档中的多模态元素，例如表格、公式、图片等，将复杂多模态知识转换为结构化的表示有助于大语言模型对这些多模态知识的理解。借助该服务，预先将各类非结构化文档提取内容成文本信息后，再把结构化的文本信息写入知识库进行向量索引构建，可以显著提升RAG知识问答、智能体知识库节点等知识问答场景的效果。该服务依赖**元景万悟智能体平台**([github项目地址](https://github.com/UnicomAI/wanwu/edit/main/README_CN.md))，需要与平台共同使用。目前服务仅支持 PDF 类型的文档，未来将支持DOC、DOCX、PNG、PPT、PPTX等非结构化文档。目前已经支持mineru解析，未来将支持如Dolphin或markitdown等更多文档解析模型能力，敬请期待！

------


## 功能介绍

支持PDF文档解析并按markdown标准格式输出，支持标题层级、表格、公式、图片等复杂多模知识高质量解析。

其中：
- 表格转换为HTML格式输出
- 公式以LaTeX语法格式输出
- 图片以Minio链接输出

同时支持云端试用与私有化部署，开源部署镜像参见：[本地部署](#本地部署)


### 文档解析的关键特点

- **多样化内容提取**：支持提取图像、图像描述、表格、表格标题和脚注
  
- **公式转换**：自动识别文档中的公式并转换为LaTeX格式
  
- **表格转换**：自动识别文档中的表格并转换为HTML格式
  
- **OCR功能**：自动检测扫描版PDF和乱码PDF，并启用OCR功能
  
- **多语言支持**：OCR功能支持多种语言的检测和识别
  
- **标准格式**：支持按Markdown标准格式输出，对大模型理解格式更友好
  
- **多种运行环境**：支持纯CPU环境运行，并支持GPU(CUDA)/NPU(适配中敬请期待)加速

## 本地部署

### 通过镜像安装(推荐)
镜像中包含python，conda, 运行服务所需要的依赖，以及MinerU服务和模型。
```bash
# arm64
docker pull crpi-6pj79y7ddzdpexs8.cn-hangzhou.personal.cr.aliyuncs.com/wanwulite/doc_parser_server:1.1-20250925-arm64
# x86_64
docker pull crpi-6pj79y7ddzdpexs8.cn-hangzhou.personal.cr.aliyuncs.com/wanwulite/doc_parser_server:1.1-20250925-amd64

# 确认是否有镜像
docker images|grep doc_parser_server
# docker run启动容器
# BFF_SERVICE_MINIO依赖万悟平台的部署，部署后可以获取到这个接口
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

### 通过源码安装
前置依赖准备： python3.10.x, pip, miniconda, git，默认端口8083
安装文档解析服务
```bash
# 克隆项目到本地环境
git clone https://github.com/UnicomAI/DocParserServer.git
cd /path/to/DocParserServer
# 创建conda环境并安装依赖
conda create -n "wanwu_doc_parser_server" python=3.10
conda activate wanwu_doc_parser_server
pip install -r requirements.txt
# 启动服务
bash start_app.sh
lsof -i:8083
# 如果需要修改默认端口号，需要修改环境变量并重启文档解析服务。否则不需要执行。
export DOC_PARSER_SERVER_PORT=your_port
bash start_app.sh
lsof -i:your_port
```
安装MinerU服务：参考MinerU[官方文档](https://github.com/opendatalab/MinerU/blob/master/README_zh-CN.md)。
通过mineru命令行测试服务是否可以正常运行
```bash
mineru -p <input_path> -o <output_path>
```

可以正常运行后，通过fast api启动MinerU服务，默认端口为8000
```bash
cd /path/to/MinerU/mineru/cli
python fast_api.py
lsof -i:8000
#如需修改mineru fast api服务默认的端口号，还需要修改环境变量并重启文档解析服务。否则不需要执行。
cd /path/to/DocParserServer
conda activate wanwu_doc_parser_server
export MINERU_ADDRESS="http://127.0.0.1:8000/file_parse"
bash start_app.sh
```

## 数据协议
### 健康检查接口
#### 概述
用于检查服务是否正常启动。
#### 请求方法
`GET /rag/health`
#### 请求参数
无
#### 响应示例
```json
{
  "code": "200", 
  "status": "healthy", 
  "service": "doc_parser_server"
}
```


### 文档处理接口
#### 概述
处理上传的文档文件，执行解析和识别任务，并返回处理结果。

#### 请求方法
`POST /rag/model_parser_file`

#### 请求参数

##### 请求头
- **Content-Type**: `multipart/form-data`

##### 请求体（Form Data）

| 参数名         | 类型           | 必选 | 描述 |
|----------------|---------------|------|------|
| `file_name`    | string        | 是   | 需要解析的文档名（如 `file_name.pdf`）。 |
| `file`         | multipart file| 是   | 需要解析的文档文件的文件流（仅支持 PDF 文档）。 |
| `extract_image`| 整数          | 否   | 是否提取图片：<br>0：不提取<br>1：提取（默认） |

#### 响应示例

##### 成功响应（200 OK）
```json
{
    "code": "200",
    "content": "#sample content title \n ## content",
    "message": "文档处理完成",
    "status": "success",
    "trace_id": "060b05bb-8356-44a4-94a6-d4812670ddcc"
}
```
##### 错误响应（400/500 failed）
```json
{
    "code": "400",
    "content": "",
    "message": "file_name is required",
    "status": "failed",
    "trace_id": "060b05bb-8356-44a4-94a6-d4812670ddcc"
}
```
#### 状态码说明

| 状态码 | 含义 |
|--------|------|
| 200    | 成功处理文档，返回结果。 |
| 400    | 请求参数错误（如未上传文件、缺少参数，参数格式不正确等）。 |
| 500    | 服务内部错误（如文件处理失败、URL 处理失败、模型异常）。 |

## 使用服务
### 通过curl调用验证
```bash
curl --location 'https:/{ip:127.0.0.1}:{port:8083}/rag/model_parser_file' \
--form 'file_name="demo.pdf"' \
--form 'file=@"/path/to/demo.pdf"'
```

返回如下：
```bash
{
  "code": "200",
  "content": "# 1.4.4 角接焊缝 角焊缝的焊喉高度 K 应不小于按下列公式计算所得之值：
  $$
K = { \sqrt { 2 } } h \quad \mathrm { ~ mm }
$$",
  "message": "文档处理完成",
  "status": "success",
  "trace_id": "df916082-072f-4019-a517-0ebb46077263"
}
```

### 基于python代码的调用
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

## 联系我们

钉钉答疑群二维码:
![文档解析答疑钉钉群二维码](https://github.com/UnicomAI/DocParserServer/blob/main/文档解析答疑钉钉群二维码.png)

钉钉答疑群链接:
https://qr.dingtalk.com/action/joingroup?code=v1,k1,pBNnQOXRnlSdYb6nUM0RdzgmYNGkZuwjTFEJKG3JrHhuRVJIwrSsXmL8oFqU5ajJ&_dt_no_comment=1&origin=11? 邀请你加入钉钉群聊万悟文档解析服务答疑群，点击进入查看详情
