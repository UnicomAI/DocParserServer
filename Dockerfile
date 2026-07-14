# ============================================================
# DocParserServer — 全量 Docker 镜像
# 包含所有模型依赖（MinerU + PaddleOCRVL）
# 镜像较大，如果只需要特定模型，请使用带后缀的变体：
#   cp Dockerfile.mineru Dockerfile        # 仅 MinerU
#   cp Dockerfile.paddleocrvl Dockerfile    # 仅 PaddleOCRVL
# ============================================================
FROM python:3.10-slim

WORKDIR /app

# paddleocr 需要的系统底层库（OpenCV 图像处理 + Paddle 推理）
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        && rm -rf /var/lib/apt/lists/*

# 复制全量依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 复制项目代码
COPY . .

# 确保日志目录存在
RUN mkdir -p logs data/images data/raw data/processed

# 暴露服务端口
EXPOSE 8083

# 启动服务
CMD ["python", "app.py"]