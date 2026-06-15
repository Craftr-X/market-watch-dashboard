@echo off
echo ========================================
echo   A股每日行情与强势观察 - 启动脚本
echo ========================================
echo.

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)
echo Python 环境正常

echo.
echo [2/3] 安装后端依赖...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)
echo 依赖安装完成

echo.
echo [3/3] 启动后端服务...
echo 后端地址: http://127.0.0.1:8000
echo API 文档: http://127.0.0.1:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.
start "A股行情后端" cmd /k "uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo 后端服务已启动！
echo.
echo 提示: 请在新窗口中启动前端
echo   cd frontend
echo   npm install
echo   npm run dev
echo.
pause
