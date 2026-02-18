# API Key Manager 启动脚本 (Windows)

Set-Location $PSScriptRoot

# 检查虚拟环境
if (-not (Test-Path "venv")) {
    Write-Host "❌ 未检测到虚拟环境，请先运行 .\install.ps1" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查 .env 文件
if (-not (Test-Path ".env")) {
    Write-Host "❌ 未检测到配置文件，请先运行 .\install.ps1" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 激活虚拟环境
& ".\venv\Scripts\Activate.ps1"

Write-Host "🚀 启动 API Key Manager..." -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Yellow
Write-Host "  前端: http://localhost:8000" -ForegroundColor White
Write-Host "  API文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "========================================"

# 启动服务
python backend\run_server.py
