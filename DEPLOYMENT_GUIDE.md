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