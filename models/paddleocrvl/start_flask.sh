#!/bin/bash
FLASK_PORT=5000
LOG_FILE="flask_service.log"
PY_CMD=python3
APP=flask_service.py

# 检查端口占用并优雅停止
PID=$(lsof -i :$FLASK_PORT | grep LISTEN | awk '{print $2}')
[ -n "$PID" ] && echo "停止占用进程$PID" && kill $PID && sleep 2

# 启动服务
nohup $PY_CMD $APP > $LOG_FILE 2>&1 &
sleep 1
PID=$(ps -ef | grep "$PY_CMD $APP" | grep -v grep | awk '{print $2}')
[ -n "$PID" ] && echo "启动成功！PID:$PID 访问:http://0.0.0.0:$FLASK_PORT" || echo "启动失败，查看$LOG_FILE"