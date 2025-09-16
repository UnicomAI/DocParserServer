#!/bin/bash

# 定义端口号和应用路径
PORT=8083
APP_PATH="/home/jovyan/lzy/doc_parser_server/app.py"

# 检查端口是否被占用
PID=$(lsof -t -i:$PORT)

if [ ! -z "$PID" ]; then
    echo "端口 $PORT 已被占用，正在杀掉进程 $PID"
    kill -9 $PID
    echo "进程 $PID 已被杀掉"
fi

# 在后台启动应用
echo "正在后台启动应用..."
nohup python $APP_PATH > app_start.log 2>&1 &
echo "应用已在后台启动，日志输出到 app_start.log"
