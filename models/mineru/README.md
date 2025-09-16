# doc_parser_server mineru



## 文档使用
如果通过mineru源码安装mineru，则可以使用脚本启动fast api服务（MinerURootDir/mineru/cli/）
start_fast_api.sh放到和fast_api.py同目录下，用于fast_api启动mineru服务，默认端口为8000，ip为127.0.0.1。
如果要外网访问，则需要修改fast_api.py中的host为0.0.0.0。
