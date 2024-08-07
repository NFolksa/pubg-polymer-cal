@echo off
REM 关闭命令提示符的回显
chcp 65001 >nul
REM 切换到 UTF-8 编码

echo 激活虚拟环境...
REM 激活虚拟环境
call venv\Scripts\activate.bat

echo 启动 Flask 应用程序...
REM 启动 Flask 应用程序
python app.py
