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

REM 保存进程ID以便后续终止
set "FLASK_PID=%!"

echo 等待应用启动...
REM 等待应用启动
timeout /t 2 >nul

echo 打开默认浏览器并访问本地服务器...
start http://127.0.0.1:5000/

REM 等待用户关闭命令窗口
pause >nul

echo 关闭 Flask 应用程序...
REM 关闭 Flask 应用程序
taskkill /F /PID %FLASK_PID%

REM 关闭命令窗口
echo 程序已终止，关闭窗口...
exit
