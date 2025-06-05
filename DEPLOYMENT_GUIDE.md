# 生產環境部署指南

## 概述
本指南將協助您將 SMART on FHIR 出血風險計算器部署到生產環境，特別是與 Cerner EHR 系統整合。

## 前置要求

### 1. Cerner 開發者註冊
- [ ] 在 [Cerner Developer Portal](https://fhir.cerner.com/) 註冊開發者帳戶
- [ ] 創建新的 SMART on FHIR 應用程式
- [ ] 獲取 Client ID 和 Client Secret
- [ ] 配置 Redirect URI (必須是 HTTPS)

### 2. 伺服器要求
- [ ] Linux 伺服器 (Ubuntu 20.04+ 或 CentOS 8+ 推薦)
- [ ] Python 3.11+
- [ ] Docker 和 Docker Compose (推薦)
- [ ] SSL 憑證 (Let's Encrypt 或商業憑證)
- [ ] 反向代理 (Nginx 推薦)

## 部署步驟

### 步驟 1: 準備伺服器環境

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安裝 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 安裝 Nginx
sudo apt install nginx -y
```

### 步驟 2: 配置 SSL 憑證

```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 獲取 SSL 憑證
sudo certbot --nginx -d yourdomain.com

# 設定自動更新
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 步驟 3: 配置應用程式

```bash
# 克隆代碼庫
git clone <your-repository-url>
cd smart_fhir_app

# 複製環境變數範本
cp production.env.template .env

# 編輯環境變數
nano .env
```

**重要環境變數配置：**
```bash
FLASK_SECRET_KEY=<生成強密碼>
SMART_CLIENT_ID=<Cerner提供的Client ID>
SMART_CLIENT_SECRET=<Cerner提供的Secret>
SMART_REDIRECT_URI=https://yourdomain.com/callback
APP_BASE_URL=https://yourdomain.com
FLASK_ENV=production
FLASK_DEBUG=false
```

### 步驟 4: 配置 Nginx

創建 Nginx 配置文件：

```bash
sudo nano /etc/nginx/sites-available/smart-fhir-app
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全標頭
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # 代理到應用程式
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康檢查端點
    location /health {
        proxy_pass http://127.0.0.1:8080/health;
        access_log off;
    }

    # 靜態文件
    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

啟用站點：
```bash
sudo ln -s /etc/nginx/sites-available/smart-fhir-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 步驟 5: 使用 Docker 部署

創建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      - FLASK_ENV=production
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./static:/app/static
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

部署應用程式：
```bash
# 構建並啟動
docker-compose up -d --build

# 檢查狀態
docker-compose ps
docker-compose logs -f app
```

### 步驟 6: 設定監控

創建系統服務監控腳本：

```bash
sudo nano /etc/systemd/system/smart-fhir-monitor.service
```

```ini
[Unit]
Description=SMART FHIR App Monitor
After=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/docker-compose -f /path/to/your/app/docker-compose.yml ps
WorkingDirectory=/path/to/your/app
User=your-user

[Install]
WantedBy=multi-user.target
```

## 安全檢查清單

### 應用程式安全
- [ ] **環境變數安全**：所有敏感資訊存儲在環境變數中
- [ ] **HTTPS 強制執行**：所有流量重定向到 HTTPS
- [ ] **安全標頭**：CSP、HSTS、X-Frame-Options 等已配置
- [ ] **Session 安全**：安全的 cookie 配置
- [ ] **輸入驗證**：所有用戶輸入已驗證

### 伺服器安全
- [ ] **防火牆配置**：只開放必要端口 (80, 443, 22)
- [ ] **SSH 安全**：禁用密碼登入，使用金鑰認證
- [ ] **系統更新**：定期更新系統和依賴
- [ ] **日誌監控**：配置日誌收集和告警
- [ ] **備份策略**：定期備份應用程式和配置

### Cerner 整合安全
- [ ] **Client Secret 保護**：安全存儲 Client Secret
- [ ] **Redirect URI 驗證**：確保 Redirect URI 正確配置
- [ ] **Scope 最小化**：只請求必要的 FHIR 權限
- [ ] **Token 管理**：適當的 token 過期和刷新機制

## 監控和維護

### 健康檢查
```bash
# 檢查應用程式健康狀態
curl https://yourdomain.com/health

# 檢查 Docker 容器狀態
docker-compose ps

# 查看應用程式日誌
docker-compose logs -f app
```

### 日誌管理
```bash
# 設定日誌輪轉
sudo nano /etc/logrotate.d/smart-fhir-app

# 內容：
/path/to/your/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 your-user your-group
}
```

### 備份腳本
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/smart-fhir-app"
APP_DIR="/path/to/your/app"

mkdir -p $BACKUP_DIR

# 備份應用程式代碼和配置
tar -czf $BACKUP_DIR/app_$DATE.tar.gz -C $APP_DIR .

# 備份 Docker 映像
docker save smart_fhir_app:latest | gzip > $BACKUP_DIR/docker_image_$DATE.tar.gz

# 清理舊備份 (保留30天)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

## 故障排除

### 常見問題

1. **HTTPS 重定向循環**
   - 檢查 Nginx 配置中的 `X-Forwarded-Proto` 標頭
   - 確認應用程式正確處理代理標頭

2. **Cerner 認證失敗**
   - 驗證 Client ID 和 Redirect URI
   - 檢查 SMART scopes 配置
   - 確認 HTTPS 憑證有效

3. **應用程式無法啟動**
   - 檢查環境變數配置
   - 查看 Docker 日誌
   - 驗證 cdss_config.json 文件

4. **效能問題**
   - 監控記憶體和 CPU 使用率
   - 檢查資料庫連接
   - 優化 FHIR API 呼叫

### 緊急聯絡資訊
- 系統管理員：[聯絡資訊]
- Cerner 技術支援：[聯絡資訊]
- 應用程式開發團隊：[聯絡資訊]

## 更新和維護

### 應用程式更新
```bash
# 拉取最新代碼
git pull origin main

# 重新構建和部署
docker-compose down
docker-compose up -d --build

# 驗證部署
curl https://yourdomain.com/health
```

### 安全更新
- 定期更新 Python 依賴：`pip list --outdated`
- 更新 Docker 基礎映像
- 監控安全漏洞通告
- 定期審查存取日誌

---

**注意**：此指南提供了基本的部署框架。根據您的具體環境和需求，可能需要額外的配置和安全措施。建議在部署前進行充分的測試，並諮詢資訊安全專家。

# Google App Engine 部署指南

## 🚨 **緊急修復 - GAE 部署錯誤解決方案**

如果您遇到 Flask 應用程式錯誤，請確認以下修復已經完成：

### 修復 1: 移除動態模板創建代碼
- ✅ 已移除 `APP.py` 中的動態模板創建代碼
- ✅ 修正了 `if __name__ == '__main__':` 條件

### 修復 2: CORS 配置衝突解決
- ✅ 修復了多重 CORS 配置衝突
- ✅ 簡化 CORS 設定以避免錯誤
- ✅ 添加 CORS 錯誤處理機制

### 修復 3: GAE 環境安全配置
- ✅ 修正 GAE 環境下的會話 cookie 設定
- ✅ 停用不必要的 HTTPS 強制重導向
- ✅ 優化 GAE 特定的安全配置

### 修復 4: 正確的 app.yaml 配置
```yaml
service: smart-calc
runtime: python311
entrypoint: gunicorn -b :$PORT APP:app

env_variables:
  SMART_CLIENT_ID: "aluminum001@gmail.com"
  SMART_REDIRECT_URI: "https://smart-calc-dot-fhir0730.df.r.appspot.com/callback"
  SMART_SCOPES: "launch/patient openid fhirUser profile email patient/Patient.read patient/Observation.read patient/Condition.read patient/MedicationRequest.read patient/Procedure.read online_access"
  FLASK_SECRET_KEY: "your-escaped-secret-key"
  APP_BASE_URL: "https://smart-calc-dot-fhir0730.df.r.appspot.com"
```

### 修復 3: 確保必要檔案存在
```bash
# 確認檔案存在
ls -la APP.py app.yaml requirements.txt cdss_config.json
ls -la templates/
```

### 立即部署命令
```bash
gcloud app deploy app.yaml --include-files cdss_config.json
```

---

## 🚀 **部署前檢查清單**

### 1. **必要文件確認**
確保以下文件存在於您的專案根目錄：
```
smart_fhir_app/
├── APP.py                    # 主應用程式檔案
├── app.yaml                  # GAE 配置檔案
├── requirements.txt          # Python 依賴套件
├── cdss_config.json         # CDSS 配置檔案 (關鍵!)
├── templates/               # HTML 模板目錄
│   ├── layout.html
│   ├── main_app.html
│   ├── error.html
│   └── ...
└── static/                  # 靜態檔案目錄
    └── ...
```

### 2. **環境變數設定**
在 `app.yaml` 中更新以下環境變數：

```yaml
env_variables:
  FLASK_SECRET_KEY: "YOUR_SECURE_SECRET_KEY_HERE"
  SMART_CLIENT_ID: "your-registered-client-id"
  SMART_REDIRECT_URI: "https://your-project-id.appspot.com/callback"
  SMART_SCOPES: "launch/patient openid fhirUser profile email patient/Patient.read patient/Observation.read patient/Condition.read patient/MedicationRequest.read online_access"
```

⚠️ **重要**: 將 `your-project-id` 替換為您的實際 GAE 專案 ID。

### 3. **CDSS 配置檔案**
確保 `cdss_config.json` 檔案存在且格式正確。如果檔案遺失，應用程式會使用 fallback 配置，但功能會受限。

## 📦 **部署步驟**

### 步驟 1: 安裝 Google Cloud SDK
```bash
# 下載並安裝 Google Cloud SDK
# https://cloud.google.com/sdk/docs/install
```

### 步驟 2: 認證和設定專案
```bash
# 登入 Google Cloud
gcloud auth login

# 設定專案 ID
gcloud config set project YOUR_PROJECT_ID

# 確認專案設定
gcloud config list
```

### 步驟 3: 確認檔案完整性
```bash
# 檢查關鍵檔案是否存在
ls -la cdss_config.json app.yaml requirements.txt APP.py

# 驗證 JSON 格式
python -m json.tool cdss_config.json > /dev/null && echo "JSON 格式正確" || echo "JSON 格式錯誤"
```

### 步驟 4: 部署應用程式
```bash
# 部署到 GAE
gcloud app deploy app.yaml

# 查看部署狀態
gcloud app browse
```

## 🔍 **部署後驗證**

### 1. **健康檢查**
訪問您的健康檢查端點：
```
https://YOUR_PROJECT_ID.appspot.com/health
```

期望的回應：
```json
{
  "status": "healthy",
  "config": {
    "status": "loaded",
    "loaded_successfully": true,
    "has_minimal_config": true
  }
}
```

### 2. **功能測試**
- 測試 SMART 授權流程
- 驗證 CDS Hooks 端點
- 檢查風險計算功能

## ❌ **常見問題與解決方案**

### 問題 1: "CDSS configuration file not found"
**原因**: `cdss_config.json` 未包含在部署中

**解決方案**:
1. 確認 `cdss_config.json` 在專案根目錄
2. 檢查 `app.yaml` 中的 `includes` 設定
3. 重新部署：`gcloud app deploy --include-files cdss_config.json`

### 問題 2: "Invalid JSON in configuration file"
**原因**: JSON 格式錯誤

**解決方案**:
```bash
# 驗證 JSON 格式
python -m json.tool cdss_config.json

# 修復格式錯誤後重新部署
```

### 問題 3: 授權錯誤
**原因**: SMART 設定不正確

**解決方案**:
1. 確認 `SMART_REDIRECT_URI` 指向正確的 GAE URL
2. 在 EHR 系統中註冊正確的 redirect URI
3. 檢查 `SMART_CLIENT_ID` 是否正確

### 問題 4: 記憶體或效能問題
**解決方案**:
1. 在 `app.yaml` 中調整 `instance_class`：
```yaml
instance_class: F4  # 更高的記憶體和 CPU
```

2. 調整自動縮放設定：
```yaml
automatic_scaling:
  min_instances: 1  # 保持至少一個實例運行
  max_instances: 20
```

## 📊 **監控和日誌**

### 查看應用程式日誌
```bash
# 即時日誌
gcloud app logs tail -s default

# 查看特定時間範圍的日誌
gcloud app logs read --limit=50
```

### 監控儀表板
訪問 Google Cloud Console:
- **App Engine > 儀表板**: 查看流量和效能
- **Logging > 日誌瀏覽器**: 詳細日誌分析
- **Error Reporting**: 錯誤追蹤

## 🔄 **更新部署**

### 更新應用程式碼
```bash
# 部署新版本
gcloud app deploy app.yaml

# 查看部署歷史
gcloud app versions list

# 切換流量到新版本（如果使用版本管理）
gcloud app services set-traffic default --splits=NEW_VERSION=1
```

### 更新 CDSS 配置
```bash
# 只更新配置檔案
gcloud app deploy app.yaml --include-files cdss_config.json
```

## 🆘 **緊急回復**

如果新部署出現問題：

```bash
# 查看可用版本
gcloud app versions list

# 回復到上一個版本
gcloud app services set-traffic default --splits=PREVIOUS_VERSION=1

# 刪除有問題的版本
gcloud app versions delete PROBLEMATIC_VERSION
```

## 📞 **技術支援**

如果遇到無法解決的問題：

1. 檢查 GAE 日誌中的詳細錯誤訊息
2. 確認所有環境變數設定正確
3. 驗證 `cdss_config.json` 格式和內容
4. 檢查 EHR 系統中的應用程式註冊設定

部署成功後，您的 SMART FHIR 應用程式應該能夠：
- ✅ 處理 SMART 授權流程
- ✅ 提供 CDS Hooks 服務
- ✅ 計算出血風險評分
- ✅ 在配置檔案缺失時使用 fallback 機制 