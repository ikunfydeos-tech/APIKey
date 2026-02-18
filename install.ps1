# API Key Manager 一键安装脚本 (Windows)
# 使用方法: 右键 -> 使用 PowerShell 运行

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  API Key Manager 安装脚本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ 检测到 $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未检测到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 检查 pip
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✅ 检测到 pip" -ForegroundColor Green
} catch {
    Write-Host "❌ 未检测到 pip" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 创建虚拟环境
if (-not (Test-Path "venv")) {
    Write-Host ""
    Write-Host "📦 创建虚拟环境..." -ForegroundColor Yellow
    python -m venv venv
}

# 激活虚拟环境
Write-Host "🔌 激活虚拟环境..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# 安装依赖
Write-Host ""
Write-Host "📥 安装依赖..." -ForegroundColor Yellow
pip install -r backend\requirements.txt

# 创建环境变量文件
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "⚙️  创建配置文件..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    
    # 生成随机密钥
    $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 43 | ForEach-Object {[char]$_})
    $encryptionKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 43 | ForEach-Object {[char]$_})
    $encryptionSalt = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})
    
    # 替换密钥
    (Get-Content ".env") -replace "your-secret-key-at-least-32-characters-long", $secretKey | Set-Content ".env"
    (Get-Content ".env") -replace "your-32-byte-encryption-key-here", $encryptionKey | Set-Content ".env"
    (Get-Content ".env") -replace "your-16-byte-salt", $encryptionSalt | Set-Content ".env"
    
    Write-Host "✅ 配置文件已创建，密钥已自动生成" -ForegroundColor Green
} else {
    Write-Host "✅ 配置文件已存在" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  ✅ 安装完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "快速启动：" -ForegroundColor Yellow
Write-Host "  .\start.ps1"
Write-Host ""
Write-Host "或手动启动：" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host "  python backend\run_server.py"
Write-Host ""
Read-Host "按回车键退出"
