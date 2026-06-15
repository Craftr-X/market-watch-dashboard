@echo off
echo ========================================
echo   A股每日行情与强势观察 - 前端启动
echo ========================================
echo.

echo [1/2] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)
echo Node.js 环境正常

echo.
echo [2/2] 启动前端服务...
cd frontend
echo 安装依赖...
call npm install
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

echo.
echo 启动开发服务器...
echo 前端地址: http://localhost:3000
echo.
echo 按 Ctrl+C 停止服务
echo.
call npm run dev
