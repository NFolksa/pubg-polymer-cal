@echo off
REM 关闭回显

REM 设置控制台为UTF-8编码
chcp 65001 > nul

REM 创建和激活虚拟环境
python -m venv venv
call venv\Scripts\activate

REM 升级pip到最新版本
python -m pip install --upgrade pip

REM 安装项目依赖
pip install -r requirements.txt

REM 安装成功消息
echo 安装完成！请使用 run.bat 启动应用程序。

REM 提示用户按任意键退出
echo.
echo 初始化完成。请按任意键退出...
pause >nul
