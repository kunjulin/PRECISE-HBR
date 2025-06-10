#!/bin/bash

# PRECISE-DAPT SMART on FHIR 應用程式
# Google Cloud Platform 部署腳本 - SMART-LU 專案

set -e  # 遇到錯誤立即退出

echo "🚀 開始部署 PRECISE-DAPT SMART on FHIR 應用程式到 Google Cloud..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案配置
PROJECT_ID="smart-lu"
SERVICE_NAME="smart-fhir-app"
REGION="us-central1"

# 檢查必要工具
echo -e "${BLUE}📋 檢查必要工具...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI 未安裝。請先安裝：https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# 檢查是否已登入 Google Cloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  尚未登入 Google Cloud。正在啟動登入流程...${NC}"
    gcloud auth login
fi

# 設置專案
echo -e "${BLUE}🔧 設置 Google Cloud 專案...${NC}"
gcloud config set project $PROJECT_ID

# 檢查專案是否存在
if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
    echo -e "${RED}❌ 專案 $PROJECT_ID 不存在或無法訪問${NC}"
    echo -e "${YELLOW}💡 請確認：${NC}"
    echo "   1. 專案 ID 正確"
    echo "   2. 您有該專案的訪問權限"
    echo "   3. 已啟用 App Engine API"
    exit 1
fi

# 啟用必要的 API
echo -e "${BLUE}🔌 啟用必要的 Google Cloud API...${NC}"
gcloud services enable appengine.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com

# 檢查是否已初始化 App Engine
if ! gcloud app describe &> /dev/null; then
    echo -e "${YELLOW}⚠️  App Engine 尚未初始化。正在初始化...${NC}"
    gcloud app create --region=$REGION
fi

# 檢查必要的配置文件
echo -e "${BLUE}📁 檢查配置文件...${NC}"
if [ ! -f "app.yaml" ]; then
    echo -e "${RED}❌ app.yaml 文件不存在${NC}"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt 文件不存在${NC}"
    exit 1
fi

if [ ! -f "cdss_config.json" ]; then
    echo -e "${RED}❌ cdss_config.json 文件不存在${NC}"
    exit 1
fi

# 檢查關鍵環境變量
echo -e "${BLUE}🔍 檢查環境變量配置...${NC}"
if grep -q "your-client-id-here" app.yaml; then
    echo -e "${YELLOW}⚠️  請更新 app.yaml 中的 SMART_CLIENT_ID${NC}"
    echo -e "${YELLOW}   目前值: your-client-id-here${NC}"
    read -p "是否要繼續部署？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ 部署已取消${NC}"
        exit 1
    fi
fi

if grep -q "your-flask-secret-key-here" app.yaml; then
    echo -e "${YELLOW}⚠️  請更新 app.yaml 中的 FLASK_SECRET_KEY${NC}"
    echo -e "${YELLOW}   建議使用隨機生成的密鑰${NC}"
    read -p "是否要繼續部署？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ 部署已取消${NC}"
        exit 1
    fi
fi

# 執行部署
echo -e "${GREEN}🚀 開始部署到 Google App Engine...${NC}"
echo -e "${BLUE}專案: $PROJECT_ID${NC}"
echo -e "${BLUE}服務: $SERVICE_NAME${NC}"
echo -e "${BLUE}區域: $REGION${NC}"

# 顯示部署確認
read -p "確認部署？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ 部署已取消${NC}"
    exit 1
fi

# 部署應用程式
gcloud app deploy app.yaml --project=$PROJECT_ID --quiet

# 檢查部署狀態
echo -e "${BLUE}📊 檢查部署狀態...${NC}"
gcloud app versions list --project=$PROJECT_ID

# 獲取應用程式 URL
APP_URL=$(gcloud app browse --project=$PROJECT_ID --no-launch-browser)

echo -e "${GREEN}✅ 部署成功！${NC}"
echo -e "${GREEN}📱 應用程式 URL: $APP_URL${NC}"
echo -e "${GREEN}📋 SMART Launch URL: $APP_URL/launch${NC}"
echo -e "${GREEN}📋 Cerner Sandbox URL: $APP_URL/launch/cerner-sandbox${NC}"

# 顯示後續步驟
echo -e "${YELLOW}📝 後續步驟：${NC}"
echo "1. 在 EHR 系統中註冊以下 Redirect URI:"
echo "   $APP_URL/callback"
echo "2. 更新 app.yaml 中的 SMART_CLIENT_ID"
echo "3. 測試 SMART on FHIR 連接"
echo "4. 配置自定義域名（可選）"

# 顯示有用的命令
echo -e "${BLUE}🔧 有用的命令：${NC}"
echo "查看日誌: gcloud app logs tail --project=$PROJECT_ID"
echo "查看版本: gcloud app versions list --project=$PROJECT_ID"
echo "停止服務: gcloud app versions stop [VERSION] --project=$PROJECT_ID"

echo -e "${GREEN}🎉 部署完成！${NC}" 