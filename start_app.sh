#!/bin/bash

# 定义端口号和应用路径
PORT=${DOC_PARSER_SERVER_PORT:-8083}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
APP_PATH="$SCRIPT_DIR/app.py"

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


# 在后台启动应用
echo "正在后台启动应用..."
nohup python $APP_PATH > "$LOG_FILE" 2>&1 &
echo "应用已在后台启动，日志输出到 app_start.log"