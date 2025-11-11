#!/bin/bash

# 定义日志文件路径
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/fast_api.log"

if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    echo "已创建日志目录: $(pwd)/$LOG_DIR"
fi

# 尝试关闭占用8000端口的进程
# 尝试关闭占用8000端口的进程
echo "Trying to kill process on port 8000..."
# 避免端口未占用时 kill 命令报错
if PID=$(lsof -t -i:8000); then
    kill -9 $PID
    echo "Killed process $PID on port 8000"
else
    echo "No process found on port 8000"
fi

# 后台启动 Flask 应用
echo "Starting Fast API..."
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
APP_PATH="$SCRIPT_DIR/fast_api.py"

nohup python "$APP_PATH" > "$LOG_FILE" 2>&1 &

echo "Fast API started. Check $LOG_FILE for logs."