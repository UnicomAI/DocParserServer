#!/bin/bash

# 定义日志文件路径
LOG_FILE="fast_api.log"

# 尝试关闭占用8000端口的进程
echo "Trying to kill process on port 8000..."
kill -9 $(lsof -t -i:8000)

# 后台启动 Flask 应用
echo "Starting Fast API..."
nohup python fast_api.py > $LOG_FILE 2>&1 &

echo "Fast API started. Check $LOG_FILE for logs."
