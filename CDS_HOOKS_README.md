# CDS Hooks for DAPT High Bleeding Risk Alert

## 概述

本應用程式現在支援 CDS Hooks 標準，提供雙重抗血小板治療（DAPT）高出血風險警示功能。

## 功能特點

### 觸發條件
CDS Hooks 警示只有在以下兩個條件**同時滿足**時才會觸發：

1. **DAPT 藥物組合**：病人正在使用以下任一組合：
   - Aspirin + Clopidogrel (阿司匹林 + 氯吡格雷)
   - Aspirin + Prasugrel (阿司匹林 + 普拉格雷)
   - Aspirin + Ticagrelor (阿司匹林 + 替格瑞洛)

2. **高出血風險**：PRECISE-DAPT 分數 ≥ 25 分

### 支援的 CDS Hooks

#### 1. 服務發現端點
- **URL**: `GET /cds-services`
- **說明**: 返回所有可用的 CDS 服務配置

#### 2. DAPT 出血風險警示服務
- **ID**: `dapt_bleeding_risk_alert`
- **Hook**: `medication-prescribe`
- **URL**: `POST /cds-services/dapt_bleeding_risk_alert`
- **觸發時機**: 當醫師開立藥物處方時

## 藥物識別機制

系統使用以下方式識別 DAPT 藥物：

### Aspirin (阿司匹林)
- **RxNorm 代碼**: 1191, 1154070, 1154071
- **常見名稱**: aspirin, acetylsalicylic acid, asa

### Clopidogrel (氯吡格雷)
- **RxNorm 代碼**: 32968, 309362
- **常見名稱**: clopidogrel, plavix

### Prasugrel (普拉格雷)
- **RxNorm 代碼**: 861634, 861635
- **常見名稱**: prasugrel, effient

### Ticagrelor (替格瑞洛)
- **RxNorm 代碼**: 1116632, 1116635
- **常見名稱**: ticagrelor, brilinta

## CDS Card 內容

當觸發警示時，系統會返回包含以下資訊的 CDS Card：

### 警示摘要
- 顯示病人正在使用 DAPT 且具有高出血風險
- 顯示 PRECISE-DAPT 分數

### 詳細建議
- 考慮縮短 DAPT 療程（3-6個月而非12個月）
- 密切監測出血事件
- 評估使用質子幫浦抑制劑（PPI）
- 定期監測血紅蛋白和腎功能
- 考慮心臟科會診

### 可執行建議
1. **查看詳細風險評估**: 啟動完整的 PRECISE-DAPT 風險計算器
2. **考慮 PPI 共同處方**: 建議開立奧美拉唑以保護胃腸道

## 使用方式

### 1. 服務發現
```bash
GET http://your-server/cds-services
```

### 2. 觸發 DAPT 警示
```bash
POST http://your-server/cds-services/dapt_bleeding_risk_alert
Content-Type: application/json

{
  "hookInstance": "unique-id",
  "fhirServer": "https://your-fhir-server",
  "hook": "medication-prescribe",
  "context": {
    "patientId": "patient-id"
  },
  "prefetch": {
    "patient": { ... },
    "medications": { ... },
    "hemoglobin": { ... },
    "creatinine": { ... },
    "wbc": { ... },
    "conditions": { ... }
  }
}
```

## 測試

使用提供的測試腳本來驗證功能：

```bash
python test_dapt_cds_hooks.py
```

測試包含：
1. **高風險 DAPT 病人**：應該觸發警示
2. **非 DAPT 病人**：不應觸發警示

## 整合指南

### EHR 系統整合
1. 在 EHR 系統中配置 CDS Hooks 服務端點
2. 設定在 `medication-prescribe` hook 時調用服務
3. 配置 prefetch 模板以提供必要的病人資料

### 必要的 Prefetch 資料
- `patient`: 病人基本資料
- `medications`: 活躍的藥物處方
- `hemoglobin`: 血紅蛋白檢驗值
- `creatinine`: 肌酐檢驗值
- `wbc`: 白血球計數
- `conditions`: 病人診斷條件

## 技術規格

- **標準**: CDS Hooks 1.0
- **FHIR 版本**: R4
- **支援的 Hook**: medication-prescribe
- **返回格式**: JSON (CDS Hooks Card format)

## 安全考量

- 系統僅在病人**同時**符合 DAPT 用藥和高出血風險時才觸發警示
- 如果 PRECISE-DAPT 計算失敗，會提供一般性的 DAPT 風險評估建議
- 所有 API 呼叫都會記錄以便除錯和審計

## 故障排除

### 常見問題

1. **無法識別 DAPT 藥物**
   - 檢查藥物的 RxNorm 代碼或名稱是否正確
   - 確認藥物狀態為 'active', 'on-hold', 或 'completed'

2. **PRECISE-DAPT 計算錯誤**
   - 檢查必要的檢驗值是否存在
   - 確認病人年齡和性別資料完整

3. **CDS Card 未顯示**
   - 驗證病人是否真的符合兩個觸發條件
   - 檢查服務端日誌以了解詳細錯誤訊息

## 日誌與監控

系統會記錄以下事件：
- CDS Hook 請求的接收和處理
- DAPT 藥物的檢測結果
- PRECISE-DAPT 分數計算
- 警示觸發或未觸發的原因

查看應用程式日誌以獲得詳細的執行資訊。 