# PRECISE-HBR 應用啟動指南

## 🚀 快速啟動

### 方法 1: 使用啟動腳本（推薦）

**Windows:**
```bash
start_app.bat
```

**Linux/Mac:**
```bash
python start_app.py
```

**啟用網絡訪問（允許其他電腦訪問）:**
```bash
python start_app.py --network
```

> **注意**: 使用 `--network` 參數後，應用將綁定到 `0.0.0.0`，允許從網絡上的其他電腦訪問。預設情況下，應用只綁定到 `localhost`（僅本地訪問）。

### 方法 2: 直接運行 Python

```bash
python APP.py
```

### 方法 3: 使用 Docker Compose

```bash
docker-compose up -d --build
```

## 🛑 停止服務

### 方法 1: 使用 Ctrl+C（推薦）

如果應用在終端中運行，直接按 `Ctrl+C` 即可停止服務。

**Windows PowerShell/CMD:**
- 按 `Ctrl+C` 停止服務

**Linux/Mac:**
- 按 `Ctrl+C` 停止服務

### 方法 2: 查找並終止進程

如果應用在後台運行或無法使用 Ctrl+C：

**Windows:**
```powershell
# 查找佔用端口 8081 的進程
netstat -ano | findstr :8081

# 終止進程（替換 PID 為實際進程 ID）
taskkill /PID <PID> /F
```

或使用 PowerShell：
```powershell
# 查找並終止 Python 進程
Get-Process python | Where-Object { $_.Path -like "*python*" } | Stop-Process -Force
```

**Linux/Mac:**
```bash
# 查找佔用端口 8081 的進程
lsof -ti:8081

# 終止進程
kill -9 $(lsof -ti:8081)

# 或查找 Python 進程
ps aux | grep python
kill -9 <PID>
```

### 方法 3: 停止 Docker 容器

如果使用 Docker Compose 啟動：

```bash
# 停止並移除容器
docker-compose down

# 或僅停止容器（保留數據）
docker-compose stop
```

## 📋 訪問所有患者

應用啟動後，您可以通過以下方式訪問所有患者：

### 1. 測試患者列表頁面（推薦）

訪問以下 URL 來查看和選擇所有患者：

```
http://localhost:8081/test-patients
```

或指定 FHIR 服務器：

```
http://localhost:8081/test-patients?server=YOUR_FHIR_SERVER_URL
```

**功能：**
- ✅ 從 FHIR 服務器實時獲取患者列表
- ✅ 顯示患者詳細信息（姓名、ID、性別、出生日期）
- ✅ 點擊患者卡片直接進入測試
- ✅ 支持直接輸入 Patient ID
- ✅ 支持切換不同的 FHIR 服務器

### 2. 快速測試模式

訪問以下 URL 使用默認測試患者：

```
http://localhost:8081/test-mode
```

或指定特定患者和服務器：

```
http://localhost:8081/test-mode?server=YOUR_FHIR_SERVER_URL&patient_id=YOUR_PATIENT_ID
```

**注意**: 如果不指定 `server` 和 `patient_id` 參數，將使用 `.env` 文件中配置的預設值。

### 3. Standalone Launch（完整 OAuth）

訪問以下 URL 進行完整的 SMART on FHIR 授權：

```
http://localhost:8081/standalone
```

## 🔧 配置您的 FHIR 服務器

### 默認 FHIR 服務器

應用通過環境變量配置預設 FHIR 服務器。在 `.env` 文件中設置：

```env
DEFAULT_FHIR_SERVER=http://your-fhir-server-url/fhir
DEFAULT_TEST_PATIENT_ID=your-default-patient-id
```

**注意**: `.env` 文件不會上傳到 Git，請根據您的實際環境配置。

### 切換 FHIR 服務器

在測試患者列表頁面，您可以：

1. **使用預設服務器按鈕**：
   - SMART Health IT
   - Logica Sandbox
   - HAPI FHIR

2. **輸入自定義服務器**：
   - 在服務器輸入框中輸入您的 FHIR 服務器 URL
   - 點擊「載入患者」按鈕

3. **通過 URL 參數**：
   ```
   http://localhost:8081/test-patients?server=YOUR_FHIR_SERVER_URL
   ```

## 📝 使用流程

### 訪問所有患者的完整流程：

1. **啟動應用**
   ```bash
   python start_app.py
   ```

2. **打開瀏覽器訪問測試患者頁面**
   ```
   http://localhost:8081/test-patients
   ```
   
   或指定 FHIR 服務器：
   ```
   http://localhost:8081/test-patients?server=YOUR_FHIR_SERVER_URL
   ```

3. **選擇患者**
   - 從列表中選擇一個患者，或
   - 在「直接輸入 Patient ID」區域輸入患者 ID

4. **查看風險評分**
   - 應用會自動載入患者數據
   - 計算 PRECISE-HBR 風險評分
   - 顯示詳細的風險分析結果

## 🎯 主要端點

| 端點 | 描述 | URL |
|------|------|-----|
| 主頁 | 應用主頁 | `http://localhost:8081/` |
| 測試患者列表 | 查看所有患者 | `http://localhost:8081/test-patients` |
| 快速測試模式 | 快速測試 | `http://localhost:8081/test-mode` |
| Standalone Launch | 完整 OAuth | `http://localhost:8081/standalone` |
| 健康檢查 | 應用狀態 | `http://localhost:8081/health` |

## ⚙️ 環境配置

確保 `.env` 文件已正確配置：

```env
FLASK_SECRET_KEY=your-secret-key
SMART_CLIENT_ID=your-client-id
SMART_REDIRECT_URI=http://localhost:8081/callback
PORT=8081
FLASK_ENV=development
FLASK_DEBUG=true

# FHIR 服務器配置（可選，如果不設置將使用代碼中的預設值）
DEFAULT_FHIR_SERVER=http://your-fhir-server-url/fhir
DEFAULT_TEST_PATIENT_ID=your-default-patient-id
```

**重要**: `.env` 文件不會上傳到 Git，請根據您的實際環境配置這些值。

## 🌐 網絡訪問配置

### 允許其他電腦訪問應用

如果您需要從網絡上的其他電腦訪問應用，請使用 `--network` 參數啟動：

```bash
python start_app.py --network
```

**重要提示：**
- 使用 `--network` 參數後，應用將綁定到 `0.0.0.0:8081`，允許網絡訪問
- 預設情況下（不使用 `--network`），應用只綁定到 `127.0.0.1:8081`（僅本地訪問）
- 啟用網絡訪問後，需要配置防火牆規則允許 port 8081

### 配置防火牆（Windows）

以管理員身份運行 PowerShell，執行：

```powershell
New-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -Description "Allow PRECISE-HBR App Network Access" -Direction Inbound -LocalPort 8081 -Protocol TCP -Action Allow -Enabled True
```

或使用提供的腳本：
```powershell
.\open_port_8081_simple.ps1
```

### 驗證網絡訪問

啟動應用後，從其他電腦訪問：
```
http://YOUR_IP_ADDRESS:8081/standalone
```

查找您的 IP 地址：
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" }
```

## 🐛 故障排除

### 應用無法啟動

1. 檢查端口 8081 是否被佔用：
   ```bash
   netstat -ano | findstr :8081
   ```

2. 檢查依賴是否已安裝：
   ```bash
   pip install -r requirements.txt
   ```

3. 檢查 .env 文件是否存在：
   ```bash
   # 如果不存在，從模板創建
   copy local.env.template .env
   ```

### 無法訪問患者數據

1. 確認 FHIR 服務器地址正確
2. 確認服務器可以訪問（無防火牆阻擋）
3. 檢查患者 ID 是否正確

### 連接被拒絕

- 確認應用正在運行
- 檢查防火牆設置
- 確認端口 8081 未被其他程序佔用

### 無法停止服務

如果使用 `Ctrl+C` 無法停止服務，可以嘗試以下方法：

1. **檢查進程是否仍在運行**：
   ```bash
   # Windows
   netstat -ano | findstr :8081
   
   # Linux/Mac
   lsof -ti:8081
   ```

2. **強制終止進程**：
   ```bash
   # Windows
   taskkill /F /IM python.exe
   
   # Linux/Mac
   pkill -9 python
   ```

3. **如果使用 Docker**：
   ```bash
   docker-compose down
   docker ps -a | grep precise-hbr
   docker kill <container_id>
   ```

4. **重啟電腦**（最後手段）

## 📞 支持

如有問題，請查看：
- `README_TEST_VERSION.md` - 測試版本說明
- `FHIR_SERVER_GUIDE.md` - FHIR 服務器配置指南

---

**最後更新**: 2025-11-13





