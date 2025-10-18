# Tradeoff Analysis Calculation Fix

## 🔴 Critical Bug Fixed: Hazard Ratio Calculation Error

**發現日期**: 2025-10-03  
**修復日期**: 2025-10-03  
**嚴重程度**: 高 - 影響風險評估的準確性

---

## 問題描述

### ❌ 錯誤的計算方式

在 `fhir_data_service.py` 中有兩個函數使用了錯誤的 Hazard Ratio (HR) 組合方式：

1. `calculate_tradeoff_scores_interactive()` - 用於互動式權衡分析
2. `calculate_tradeoff_scores()` - 用於初始評估

**錯誤代碼** (line 548, 555, 687, 690):
```python
# ❌ 錯誤：直接相加 HR
bleeding_score_hr += predictor['hazardRatio']
thrombotic_score_hr += predictor['hazardRatio']
```

### 為什麼這是錯誤的？

在 **Cox 比例風險模型** (Cox Proportional Hazards Model) 中：

- **Hazard Ratios 應該相乘**，而不是相加
- 或者在對數尺度上相加：`log(Total HR) = log(HR₁) + log(HR₂) + log(HR₃)`

### 錯誤計算的實例

假設患者有以下風險因子：
- Age ≥ 65 years (HR: 1.50)
- Current smoker (HR: 1.47)
- Hemoglobin < 11 g/dL (HR: 3.99)

**錯誤計算** (相加):
```
Total HR = 1.50 + 1.47 + 3.99 = 6.96
出血風險 = 2.5% × 6.96 = 17.4%
```

**正確計算** (相乘):
```
Total HR = 1.50 × 1.47 × 3.99 = 8.79
出血風險 = 2.5% × 8.79 = 22.0%
```

**誤差**: ~26% 低估風險！

---

## ✅ 修復方案

### 修復的代碼

**1. `calculate_tradeoff_scores_interactive()`**

```python
# ✅ 修復前：
bleeding_score_hr = 0
for predictor in model_predictors['bleedingEvents']['predictors']:
    if active_factors.get(factor_key, False):
        bleeding_score_hr += predictor['hazardRatio']  # ❌

# ✅ 修復後：
bleeding_score_hr = 1.0  # Start with HR = 1 (no risk factors)
for predictor in model_predictors['bleedingEvents']['predictors']:
    if active_factors.get(factor_key, False):
        bleeding_score_hr *= predictor['hazardRatio']  # ✅ MULTIPLY
```

**2. `calculate_tradeoff_scores()`**

```python
# ✅ 修復前：
bleeding_score = 0
def add_score(event_type, factor, ratio):
    if event_type == 'bleeding':
        bleeding_score += ratio  # ❌

# ✅ 修復後：
bleeding_score = 1.0  # Start with HR = 1
def add_score(event_type, factor, ratio):
    if event_type == 'bleeding':
        bleeding_score *= ratio  # ✅ MULTIPLY
```

### 初始值的重要性

- **修復前**: `bleeding_score_hr = 0` (錯誤)
- **修復後**: `bleeding_score_hr = 1.0` (正確)

當沒有風險因子時：
- HR = 1.0 表示「無額外風險」
- HR = 0 沒有數學意義

---

## 數學原理

### Cox 比例風險模型

在 Cox 模型中，風險函數定義為：

```
h(t|X) = h₀(t) × exp(β₁X₁ + β₂X₂ + ... + βₙXₙ)
```

其中：
- `h(t|X)` = 給定協變量 X 的風險函數
- `h₀(t)` = 基線風險函數
- `β` = 回歸係數
- `X` = 協變量（風險因子）

**Hazard Ratio** 定義為：
```
HR = exp(β)
```

當有多個風險因子時：
```
Total HR = exp(β₁ + β₂ + ... + βₙ) = exp(β₁) × exp(β₂) × ... × exp(βₙ)
         = HR₁ × HR₂ × ... × HRₙ
```

**因此，HR 必須相乘！**

### 對數尺度的等價性

使用對數：
```python
import math
log_hr_sum = sum(math.log(hr) for hr in [1.50, 1.47, 3.99])
total_hr = math.exp(log_hr_sum)  # = 8.79
```

---

## 影響評估

### 對風險評估的影響

| 風險因子組合 | 錯誤 (相加) | 正確 (相乘) | 誤差 |
|------------|-----------|-----------|------|
| 1 個因子 (HR=1.5) | 1.5 | 1.5 | 0% |
| 2 個因子 (HR=1.5, 1.5) | 3.0 | 2.25 | +33% 高估 |
| 3 個因子 (HR=1.5, 1.5, 2.0) | 5.0 | 4.5 | +11% 高估 |
| 真實案例 (HR=1.5, 1.47, 3.99) | 6.96 | 8.79 | **-26% 低估** ⚠️ |

### 臨床意義

- **低估風險**: 可能導致醫生低估患者的出血風險
- **錯誤的風險分層**: 患者可能被錯誤分類為低風險組
- **治療決策**: 可能影響抗血小板治療的持續時間決策

---

## 驗證測試

### 測試案例 1: 單一風險因子

**輸入**: Age ≥ 65 years (HR: 1.50)

```python
# 修復前: 0 + 1.50 = 1.50 ✓
# 修復後: 1.0 × 1.50 = 1.50 ✓
# 結果: 一致（單一因子無差異）
```

### 測試案例 2: 多個風險因子

**輸入**: 
- Age ≥ 65 (HR: 1.50)
- Current smoker (HR: 1.47)  
- Hemoglobin < 11 g/dL (HR: 3.99)

```python
# 修復前: 1.50 + 1.47 + 3.99 = 6.96
# 修復後: 1.50 × 1.47 × 3.99 = 8.79
# 風險: 2.5% × 6.96 = 17.4% (錯誤)
#      2.5% × 8.79 = 22.0% (正確)
```

### 測試案例 3: 血栓風險

**輸入**: Prior MI (HR: 1.89)

```python
# 修復前: 0 + 1.89 = 1.89
# 修復後: 1.0 × 1.89 = 1.89
# 風險: 3.0% × 1.89 = 5.67%
```

---

## 部署資訊

### 受影響的文件
- `fhir_data_service.py` (2 個函數修復)
  - `calculate_tradeoff_scores_interactive()` (line 529-568)
  - `calculate_tradeoff_scores()` (line 624-745)

### 修復版本
- **版本**: 20251003t234500 (預計)
- **部署 URL**: https://smart-lu.uc.r.appspot.com

### 測試建議

1. ✅ 重新測試權衡分析頁面
2. ✅ 驗證多個風險因子組合
3. ✅ 確認圖表顯示正確的風險點
4. ✅ 比對修復前後的風險評估結果

---

## 文獻參考

1. **Cox, D. R. (1972)**. "Regression Models and Life-Tables". *Journal of the Royal Statistical Society. Series B (Methodological)*, 34(2), 187-220.

2. **Urban P, et al. (2019)**. "Defining High Bleeding Risk in Patients Undergoing Percutaneous Coronary Intervention: A Consensus Document from the Academic Research Consortium for High Bleeding Risk". *Circulation*, 140:240-261.

3. **Galli M, et al. (2021)**. "Assessing the Risks of Bleeding vs Thrombotic Events in Patients at High Bleeding Risk After Coronary Stent Implantation: The ARC-High Bleeding Risk Trade-off Model". *JAMA Cardiology*, 6(4):410-419.

---

## 結論

這個修復確保了風險評估符合 **Cox 比例風險模型** 的數學基礎，提供了更準確的臨床決策支持。

**感謝用戶發現並報告這個重要問題！** 🙏

