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

### 方法 2: 直接運行 Python

```bash
python APP.py
```

### 方法 3: 使用 Docker Compose

```bash
docker-compose up -d --build
```

## 📋 訪問所有患者

應用啟動後，您可以通過以下方式訪問所有患者：

### 1. 測試患者列表頁面（推薦）

訪問以下 URL 來查看和選擇所有患者：

```
http://localhost:8080/test-patients?server=http://10.29.99.18:9091/fhir/
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
http://localhost:8080/test-mode
```

或指定特定患者：

```
http://localhost:8080/test-mode?server=http://10.29.99.18:9091/fhir/&patient_id=0322400H12092976400000000000000
```

### 3. Standalone Launch（完整 OAuth）

訪問以下 URL 進行完整的 SMART on FHIR 授權：

```
http://localhost:8080/standalone
```

## 🔧 配置您的 FHIR 服務器

### 默認 FHIR 服務器

應用已配置為使用您的 FHIR 服務器：
- **服務器地址**: `http://10.29.99.18:9091/fhir/`
- **FHIR 版本**: R4 (4.0.1)

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
   http://localhost:8080/test-patients?server=YOUR_FHIR_SERVER_URL
   ```

## 📝 使用流程

### 訪問所有患者的完整流程：

1. **啟動應用**
   ```bash
   python start_app.py
   ```

2. **打開瀏覽器訪問測試患者頁面**
   ```
   http://localhost:8080/test-patients?server=http://10.29.99.18:9091/fhir/
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
| 主頁 | 應用主頁 | `http://localhost:8080/` |
| 測試患者列表 | 查看所有患者 | `http://localhost:8080/test-patients` |
| 快速測試模式 | 快速測試 | `http://localhost:8080/test-mode` |
| Standalone Launch | 完整 OAuth | `http://localhost:8080/standalone` |
| 健康檢查 | 應用狀態 | `http://localhost:8080/health` |

## ⚙️ 環境配置

確保 `.env` 文件已正確配置：

```env
FLASK_SECRET_KEY=your-secret-key
SMART_CLIENT_ID=your-client-id
SMART_REDIRECT_URI=http://localhost:8080/callback
PORT=8080
FLASK_ENV=development
FLASK_DEBUG=true
```

## 🐛 故障排除

### 應用無法啟動

1. 檢查端口 8080 是否被佔用：
   ```bash
   netstat -ano | findstr :8080
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
- 確認端口 8080 未被其他程序佔用

## 📞 支持

如有問題，請查看：
- `README_TEST_VERSION.md` - 測試版本說明
- `FHIR_SERVER_GUIDE.md` - FHIR 服務器配置指南

---

**最後更新**: 2025-11-13





