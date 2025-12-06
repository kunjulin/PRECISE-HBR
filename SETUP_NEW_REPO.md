# 設置新的獨立 Git 倉庫指南

## 選項 1: 創建全新的 Git 倉庫（推薦）

如果您想要完全獨立的新倉庫，不保留現有的 Git 歷史：

### 步驟 1: 移除現有的 Git 連接

```bash
# 移除現有的遠程倉庫連接
git remote remove origin

# 或者完全移除 Git 歷史（可選）
# 警告：這會刪除所有 Git 歷史記錄
# rm -rf .git
```

### 步驟 2: 初始化新的 Git 倉庫

```bash
# 初始化新的 Git 倉庫
git init

# 添加所有文件
git add .

# 創建初始提交
git commit -m "Initial commit: PRECISE-HBR SMART on FHIR Application"

# 添加新的遠程倉庫（替換為您的倉庫 URL）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 推送到新倉庫
git branch -M main
git push -u origin main
```

## 選項 2: 保留歷史記錄，更換遠程倉庫

如果您想保留現有的 Git 歷史，但連接到新的遠程倉庫：

### 步驟 1: 移除舊的遠程倉庫

```bash
git remote remove origin
```

### 步驟 2: 添加新的遠程倉庫

```bash
# 添加新的遠程倉庫（替換為您的倉庫 URL）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 推送到新倉庫
git push -u origin main
```

## 選項 3: 創建新的分支並推送到新倉庫

如果您想保留兩個倉庫的連接：

```bash
# 添加新的遠程倉庫
git remote add new-origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 推送到新倉庫
git push -u new-origin main
```

## 重要文件檢查清單

在推送到新倉庫前，請確保以下敏感文件已被 `.gitignore` 排除：

- ✅ `.env` - 環境變量文件（包含敏感信息）
- ✅ `instance/` - 實例數據（會話、審計日誌等）
- ✅ `__pycache__/` - Python 緩存文件
- ✅ `*.log` - 日誌文件

## 創建 GitHub 新倉庫

1. 登錄 GitHub
2. 點擊右上角的 "+" → "New repository"
3. 填寫倉庫名稱（例如：`PRECISE-HBR-SMART-App`）
4. 選擇 Public 或 Private
5. **不要**初始化 README、.gitignore 或 license（因為本地已有）
6. 點擊 "Create repository"
7. 複製倉庫 URL（例如：`https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git`）

## 推送前的最後檢查

```bash
# 檢查將要提交的文件
git status

# 檢查 .gitignore 是否正確
cat .gitignore

# 確保敏感文件不會被提交
git check-ignore -v .env instance/
```

## 常見問題

### Q: 如何完全移除 Git 歷史並重新開始？

```bash
# 移除 .git 目錄（刪除所有歷史）
rm -rf .git

# 重新初始化
git init
git add .
git commit -m "Initial commit"
```

### Q: 如何將代碼推送到多個遠程倉庫？

```bash
# 添加多個遠程倉庫
git remote add origin https://github.com/user1/repo1.git
git remote add backup https://github.com/user2/repo2.git

# 推送到所有遠程倉庫
git push origin main
git push backup main
```

### Q: 如何確保敏感信息不會被提交？

```bash
# 檢查 .gitignore
cat .gitignore

# 如果已經提交了敏感文件，需要從歷史中移除
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
```

