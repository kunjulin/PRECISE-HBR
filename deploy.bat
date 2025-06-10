@echo off
setlocal enabledelayedexpansion

:: PRECISE-DAPT SMART on FHIR 應用程式
:: Google Cloud Platform 部署腳本 - SMART-LU 專案 (Windows 版本)

echo 🚀 開始部署 PRECISE-DAPT SMART on FHIR 應用程式到 Google Cloud...

:: 專案配置
set PROJECT_ID=smart-lu
set SERVICE_NAME=smart-fhir-app
set REGION=us-central1

:: 檢查 Google Cloud CLI
echo 📋 檢查 Google Cloud CLI...
gcloud version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Google Cloud CLI 未安裝或未在 PATH 中
    echo 請先安裝：https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

:: 檢查登入狀態
echo 🔐 檢查 Google Cloud 登入狀態...
gcloud auth list --filter=status:ACTIVE --format="value(account)" > temp_auth.txt 2>nul
set /p AUTH_ACCOUNT=< temp_auth.txt
del temp_auth.txt

if "!AUTH_ACCOUNT!"=="" (
    echo ⚠️  尚未登入 Google Cloud。正在啟動登入流程...
    gcloud auth login
    if %errorlevel% neq 0 (
        echo ❌ 登入失敗
        pause
        exit /b 1
    )
)

:: 設置專案
echo 🔧 設置 Google Cloud 專案...
gcloud config set project %PROJECT_ID%
if %errorlevel% neq 0 (
    echo ❌ 無法設置專案 %PROJECT_ID%
    pause
    exit /b 1
)

:: 檢查專案存在性
echo 🔍 檢查專案存在性...
gcloud projects describe %PROJECT_ID% >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 專案 %PROJECT_ID% 不存在或無法訪問
    echo 💡 請確認：
    echo    1. 專案 ID 正確
    echo    2. 您有該專案的訪問權限
    echo    3. 已啟用 App Engine API
    pause
    exit /b 1
)

:: 啟用 API
echo 🔌 啟用必要的 Google Cloud API...
echo 正在啟用 App Engine API...
gcloud services enable appengine.googleapis.com --project=%PROJECT_ID%
echo 正在啟用 Cloud Build API...
gcloud services enable cloudbuild.googleapis.com --project=%PROJECT_ID%
echo 正在啟用 Logging API...
gcloud services enable logging.googleapis.com --project=%PROJECT_ID%

:: 檢查 App Engine 初始化
echo 🏗️  檢查 App Engine 狀態...
gcloud app describe --project=%PROJECT_ID% >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  App Engine 尚未初始化。正在初始化...
    gcloud app create --region=%REGION% --project=%PROJECT_ID%
    if %errorlevel% neq 0 (
        echo ❌ App Engine 初始化失敗
        pause
        exit /b 1
    )
)

:: 檢查配置文件
echo 📁 檢查配置文件...
if not exist "app.yaml" (
    echo ❌ app.yaml 文件不存在
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ❌ requirements.txt 文件不存在
    pause
    exit /b 1
)

if not exist "cdss_config.json" (
    echo ❌ cdss_config.json 文件不存在
    pause
    exit /b 1
)

:: 檢查環境變量
echo 🔍 檢查環境變量配置...
findstr /C:"your-client-id-here" app.yaml >nul
if %errorlevel% equ 0 (
    echo ⚠️  請更新 app.yaml 中的 SMART_CLIENT_ID
    echo    目前值: your-client-id-here
    set /p CONTINUE="是否要繼續部署？(y/N) "
    if /i not "!CONTINUE!"=="y" (
        echo ❌ 部署已取消
        pause
        exit /b 1
    )
)

findstr /C:"your-flask-secret-key-here" app.yaml >nul
if %errorlevel% equ 0 (
    echo ⚠️  請更新 app.yaml 中的 FLASK_SECRET_KEY
    echo    建議使用隨機生成的密鑰
    echo    建議的密鑰: b67c62ddcbe390c4bbb5cda1f71ae368288bb83a6d194d6a1cba017769ec4357
    set /p CONTINUE="是否要繼續部署？(y/N) "
    if /i not "!CONTINUE!"=="y" (
        echo ❌ 部署已取消
        pause
        exit /b 1
    )
)

:: 執行部署
echo 🚀 開始部署到 Google App Engine...
echo 專案: %PROJECT_ID%
echo 服務: %SERVICE_NAME%
echo 區域: %REGION%
echo.

set /p CONFIRM="確認部署？(y/N) "
if /i not "!CONFIRM!"=="y" (
    echo ❌ 部署已取消
    pause
    exit /b 1
)

echo 正在部署...
gcloud app deploy app.yaml --project=%PROJECT_ID% --quiet
if %errorlevel% neq 0 (
    echo ❌ 部署失敗
    pause
    exit /b 1
)

:: 檢查部署狀態
echo 📊 檢查部署狀態...
gcloud app versions list --project=%PROJECT_ID%

:: 獲取應用程式 URL
echo 🌐 獲取應用程式 URL...
for /f "tokens=*" %%i in ('gcloud app browse --project=%PROJECT_ID% --no-launch-browser 2^>nul') do set APP_URL=%%i

echo.
echo ✅ 部署成功！
echo 📱 應用程式 URL: !APP_URL!
echo 📋 SMART Launch URL: !APP_URL!/launch
echo 📋 Cerner Sandbox URL: !APP_URL!/launch/cerner-sandbox
echo.

:: 顯示後續步驟
echo 📝 後續步驟：
echo 1. 在 EHR 系統中註冊以下 Redirect URI:
echo    !APP_URL!/callback
echo 2. 更新 app.yaml 中的 SMART_CLIENT_ID
echo 3. 測試 SMART on FHIR 連接
echo 4. 配置自定義域名（可選）
echo.

:: 顯示有用的命令
echo 🔧 有用的命令：
echo 查看日誌: gcloud app logs tail --project=%PROJECT_ID%
echo 查看版本: gcloud app versions list --project=%PROJECT_ID%
echo 停止服務: gcloud app versions stop [VERSION] --project=%PROJECT_ID%
echo.

echo 🎉 部署完成！
pause 