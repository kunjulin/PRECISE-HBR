# Tradeoff Risk Calculation Fix

## 問題描述

用戶發現出血風險（Bleeding）vs. 血栓風險（Ischemic/Thrombotic）的權衡分析計算結果可能不準確，特別是當多個風險因子疊加時，計算出的風險值過高，不符合臨床實際。

## 根本原因

經過分析，發現問題出在 `convert_hr_to_probability()` 函數中：

### 原始問題代碼：
```python
def convert_hr_to_probability(total_hr_score, baseline_event_rate):
    # 簡單的線性模型（不準確）
    estimated_probability = baseline_event_rate * total_hr_score
    return round(min(estimated_probability, 100.0), 2)
```

**問題：**
1. **線性模型過於簡化**：當 HR = 2 時，風險 = 基線率 × 2。這對於小 HR 值（1-2）尚可接受，但當多個風險因子相乘導致總 HR > 5 時，會嚴重高估風險。
2. **不符合 Cox 比例風險模型**：醫學統計中的 HR（Hazard Ratio）應該使用指數模型，而非線性模型。

## 解決方案

### 1. 改進 HR 到概率的轉換公式

使用基於 **Cox 比例風險模型** 的正確公式：

```python
def convert_hr_to_probability(total_hr_score, baseline_event_rate):
    """
    使用 Cox 比例風險模型:
    P(event) = 1 - exp(-baseline_hazard × HR)
    
    其中 baseline_hazard = -ln(1 - baseline_rate)
    """
    import math
    
    # 將基線事件率（百分比）轉換為基線風險
    baseline_rate_decimal = baseline_event_rate / 100.0
    
    if baseline_rate_decimal >= 1.0:
        return 100.0
    
    # 計算基線風險（1 年內的累積風險）
    baseline_hazard = -math.log(1 - baseline_rate_decimal)
    
    # 應用 HR 得到調整後的風險
    adjusted_hazard = baseline_hazard * total_hr_score
    
    # 使用生存函數轉換回概率
    survival_probability = math.exp(-adjusted_hazard)
    event_probability = 1 - survival_probability
    
    # 轉換為百分比並四捨五入
    event_probability_percent = event_probability * 100.0
    
    return round(min(event_probability_percent, 100.0), 2)
```

**優點：**
- ✅ 當 HR = 1 時，P(event) = baseline_rate（正確）
- ✅ 當 HR 增加時，P(event) 呈非線性增長（更符合實際）
- ✅ P(event) 永遠不會超過 100%
- ✅ 符合 Cox 比例風險模型的統計學原理

### 2. 調整基線風險率

將基線風險率調整為更符合**參考組**（無風險因子的患者）的水平：

```python
# 修改前：
BASELINE_BLEEDING_RATE = 2.5  # %
BASELINE_THROMBOTIC_RATE = 3.0 # %

# 修改後：
BASELINE_BLEEDING_RATE = 1.5  # % (BARC 3-5 出血，參考組)
BASELINE_THROMBOTIC_RATE = 2.0 # % (MI/ST，參考組)
```

**理由：**
- 基線率應該代表「參考組」（hemoglobin ≥13 g/dL, eGFR ≥60 mL/min, 無合併症）的風險
- 原先設定的 2.5% 和 3.0% 更接近整體隊列的平均風險，而非參考組風險

## 數學推導

### Cox 比例風險模型

在 Cox 模型中：

\[
h(t) = h_0(t) \times HR
\]

其中：
- \( h(t) \) 是瞬時風險（hazard）
- \( h_0(t) \) 是基線風險
- \( HR \) 是風險比

累積風險（Cumulative Hazard）：

\[
H(t) = \int_0^t h(s) ds = H_0(t) \times HR
\]

生存概率（Survival Probability）：

\[
S(t) = e^{-H(t)} = e^{-H_0(t) \times HR}
\]

事件概率（Event Probability）：

\[
P(event) = 1 - S(t) = 1 - e^{-H_0(t) \times HR}
\]

從基線事件率反推基線累積風險：

\[
H_0(t) = -\ln(1 - P_0)
\]

其中 \( P_0 \) 是基線事件率。

### 範例計算

假設：
- 基線出血率 = 1.5%
- 患者有以下風險因子：
  - 年齡 ≥65 歲（HR = 1.50）
  - 血紅蛋白 < 11 g/dL（HR = 3.99）
  - 總 HR = 1.50 × 3.99 = 5.985

**使用舊公式（線性模型）：**
```
風險 = 1.5% × 5.985 = 8.98%
```

**使用新公式（Cox 模型）：**
```
baseline_hazard = -ln(1 - 0.015) = 0.01508
adjusted_hazard = 0.01508 × 5.985 = 0.0903
風險 = 1 - exp(-0.0903) = 8.64%
```

在這個例子中，差異不大。但當 HR 更大時（例如 HR = 10），差異會變得顯著：

**HR = 10 的情況：**
- 舊公式：1.5% × 10 = 15%
- 新公式：1 - exp(-0.01508 × 10) = 14.0%

**HR = 20 的情況（極端情況）：**
- 舊公式：1.5% × 20 = 30%
- 新公式：1 - exp(-0.01508 × 20) = 26.1%

可以看出，HR 越大，新公式越能防止風險被過度高估。

## 影響範圍

### 受影響的文件：
- `fhir_data_service.py` - 核心風險計算邏輯

### 受影響的功能：
- Tradeoff Analysis（出血 vs. 血栓風險權衡分析）頁面
- `/api/calculate_tradeoff` API 端點

### 不受影響的功能：
- PRECISE-HBR 風險評分計算（使用不同的計算方法）
- 其他風險評估功能

## 驗證與測試

### 測試場景 1：無風險因子
- **輸入：** 所有風險因子 = False
- **預期 HR：** 1.0
- **預期出血風險：** ≈ 1.5%
- **預期血栓風險：** ≈ 2.0%

### 測試場景 2：單一風險因子
- **輸入：** 僅 diabetes = True (HR = 1.56)
- **預期出血風險：** ≈ 1.5% (diabetes 不是出血風險因子)
- **預期血栓風險：** ≈ 3.1%

### 測試場景 3：多重風險因子
- **輸入：** smoker = True (HR = 1.47), hemoglobin_lt_11 = True (HR = 3.99)
- **預期總 HR：** 1.47 × 3.99 = 5.86
- **預期出血風險：** ≈ 8.6%

### 測試場景 4：極端情況
- **輸入：** 所有出血風險因子 = True
- **預期：** 風險應 < 100%，且符合臨床合理性

## 臨床意義

這次修正確保了：

1. **更準確的風險評估**：風險計算更符合統計學原理和臨床實際。
2. **避免過度高估**：防止多重風險因子疊加時產生不切實際的高風險值。
3. **提升臨床決策信心**：醫生可以更信任計算結果，用於指導抗血栓治療決策。

## 參考文獻

1. Gragnano F, et al. "Derivation and Validation of the PRECISE-HBR Score to Predict Bleeding After Percutaneous Coronary Intervention." *Circulation*. 2025;151(6):343-355.

2. Cox DR. "Regression Models and Life-Tables." *Journal of the Royal Statistical Society: Series B (Methodological)*. 1972;34(2):187-202.

## 總結

通過將風險計算從簡單的線性模型改為基於 Cox 比例風險模型的指數函數，我們顯著提升了 Tradeoff Analysis 的準確性和臨床實用性。這一改進確保了即使在極端情況下（多重風險因子），計算結果也能保持合理和可信。


