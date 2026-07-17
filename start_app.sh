#!/bin/bash

# 定义端口号和应用路径
PORT=${DOC_PARSER_SERVER_PORT:-8083}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
APP_PATH="$SCRIPT_DIR/app.py"
MODEL_TYPE=${MODEL_TYPE:-mineru}

# 检查端口是否被占用
PID=$(lsof -t -i:$PORT)

if [ ! -z "$PID" ]; then
    echo "端口 $PORT 已被占用，正在杀掉进程 $PID"
    kill -9 $PID
    echo "进程 $PID 已被杀掉"
fi

LOG_DIR="logs"
LOG_FILE="$LOG_DIR/app_start.log"
# 检查并创建日志目录（如果不存在）
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    echo "已创建日志目录: $(pwd)/$LOG_DIR"  # 显示绝对路径方便确认
fi

# 启动主服务
echo "正在启动主服务 (MODEL_TYPE=$MODEL_TYPE)..."
nohup python "$APP_PATH" > "$LOG_FILE" 2>&1 &
echo "主服务已启动，日志输出到 $LOG_FILE"

# 如果是 paddleocrvl，额外启动 paddleocrvl 推理服务（5000 端口）
if [ "$MODEL_TYPE" = "paddleocrvl" ]; then
    PADDLE_APP_PATH="$SCRIPT_DIR/models/paddleocrvl/app.py"
    PADDLE_LOG_FILE="$LOG_DIR/paddleocrvl_server.log"
    echo "检测到 MODEL_TYPE=paddleocrvl，正在启动 PaddleOCRVL 推理服务..."
    nohup python "$PADDLE_APP_PATH" > "$PADDLE_LOG_FILE" 2>&1 &
    echo "PaddleOCRVL 推理服务已启动，日志输出到 $PADDLE_LOG_FILE"
fi