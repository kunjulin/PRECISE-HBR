# 設置新的獨立 Git 倉庫腳本
# 使用方法: .\setup_new_repo.ps1

Write-Host "========================================"
Write-Host "設置新的獨立 Git 倉庫"
Write-Host "========================================"
Write-Host ""

# 檢查當前 Git 狀態
Write-Host "1. 檢查當前 Git 狀態..."
Write-Host ""

if (-not (Test-Path .git)) {
    Write-Host "✗ 未找到 Git 倉庫，正在初始化..." -ForegroundColor Yellow
    git init
    Write-Host "✓ Git 倉庫已初始化" -ForegroundColor Green
} else {
    Write-Host "✓ Git 倉庫已存在" -ForegroundColor Green
}

Write-Host ""
Write-Host "當前遠程倉庫:"
git remote -v 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  無遠程倉庫" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "未提交的更改:"
$status = git status --short 2>$null
if ($status) {
    Write-Host $status
} else {
    Write-Host "  無未提交的更改" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================"
Write-Host "請選擇操作:"
Write-Host "========================================"
Write-Host ""
Write-Host "1. 提交當前更改並推送到現有倉庫"
Write-Host "2. 更換遠程倉庫（保留歷史記錄）"
Write-Host "3. 創建全新的 Git 倉庫（移除歷史記錄）"
Write-Host "4. 僅查看狀態，不執行任何操作"
Write-Host ""

$choice = Read-Host "請輸入選項 (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "正在提交當前更改..."
        
        # 添加所有更改
        git add .
        
        # 提交
        $commitMessage = Read-Host "請輸入提交訊息（或按 Enter 使用預設訊息）"
        if ([string]::IsNullOrWhiteSpace($commitMessage)) {
            $commitMessage = "Update: Add network access support and preset configurations"
        }
        
        git commit -m $commitMessage
        
        Write-Host ""
        Write-Host "是否推送到遠程倉庫？" -ForegroundColor Yellow
        $push = Read-Host "輸入 y 推送，其他鍵跳過"
        if ($push -eq "y" -or $push -eq "Y") {
            git push origin main
            Write-Host "✓ 已推送到遠程倉庫" -ForegroundColor Green
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "更換遠程倉庫（保留歷史記錄）"
        Write-Host ""
        
        # 移除現有遠程倉庫
        $currentRemote = git remote show origin 2>$null | Select-String "Fetch URL" | ForEach-Object { $_.ToString().Split(":")[1].Trim() }
        if ($currentRemote) {
            Write-Host "當前遠程倉庫: $currentRemote"
            Write-Host ""
            $confirm = Read-Host "確定要移除現有遠程倉庫連接嗎？(y/n)"
            if ($confirm -eq "y" -or $confirm -eq "Y") {
                git remote remove origin
                Write-Host "✓ 已移除舊的遠程倉庫連接" -ForegroundColor Green
            } else {
                Write-Host "操作已取消"
                exit
            }
        }
        
        # 添加新的遠程倉庫
        Write-Host ""
        $newRepoUrl = Read-Host "請輸入新的 GitHub 倉庫 URL (例如: https://github.com/USERNAME/REPO_NAME.git)"
        
        if ([string]::IsNullOrWhiteSpace($newRepoUrl)) {
            Write-Host "✗ 未輸入 URL，操作已取消" -ForegroundColor Red
            exit
        }
        
        git remote add origin $newRepoUrl
        Write-Host "✓ 已添加新的遠程倉庫: $newRepoUrl" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "是否現在推送到新倉庫？" -ForegroundColor Yellow
        $push = Read-Host "輸入 y 推送，其他鍵跳過"
        if ($push -eq "y" -or $push -eq "Y") {
            git branch -M main
            git push -u origin main
            Write-Host "✓ 已推送到新倉庫" -ForegroundColor Green
        }
    }
    
    "3" {
        Write-Host ""
        Write-Host "⚠️  警告: 這將刪除所有 Git 歷史記錄！" -ForegroundColor Red
        Write-Host ""
        $confirm = Read-Host "確定要創建全新的 Git 倉庫嗎？(輸入 'yes' 確認)"
        
        if ($confirm -ne "yes") {
            Write-Host "操作已取消"
            exit
        }
        
        # 備份當前 .git（可選）
        Write-Host ""
        Write-Host "正在移除現有 Git 歷史..."
        Remove-Item -Recurse -Force .git
        Write-Host "✓ 已移除舊的 Git 歷史" -ForegroundColor Green
        
        # 初始化新倉庫
        Write-Host ""
        Write-Host "正在初始化新的 Git 倉庫..."
        git init
        Write-Host "✓ Git 倉庫已初始化" -ForegroundColor Green
        
        # 添加文件
        Write-Host ""
        Write-Host "正在添加文件..."
        git add .
        Write-Host "✓ 文件已添加" -ForegroundColor Green
        
        # 提交
        Write-Host ""
        $commitMessage = Read-Host "請輸入初始提交訊息（或按 Enter 使用預設訊息）"
        if ([string]::IsNullOrWhiteSpace($commitMessage)) {
            $commitMessage = "Initial commit: PRECISE-HBR SMART on FHIR Application"
        }
        
        git commit -m $commitMessage
        Write-Host "✓ 初始提交已創建" -ForegroundColor Green
        
        # 添加遠程倉庫
        Write-Host ""
        $newRepoUrl = Read-Host "請輸入新的 GitHub 倉庫 URL (或按 Enter 稍後添加)"
        if (-not [string]::IsNullOrWhiteSpace($newRepoUrl)) {
            git remote add origin $newRepoUrl
            Write-Host "✓ 已添加遠程倉庫: $newRepoUrl" -ForegroundColor Green
            
            Write-Host ""
            Write-Host "是否現在推送到新倉庫？" -ForegroundColor Yellow
            $push = Read-Host "輸入 y 推送，其他鍵跳過"
            if ($push -eq "y" -or $push -eq "Y") {
                git branch -M main
                git push -u origin main
                Write-Host "✓ 已推送到新倉庫" -ForegroundColor Green
            }
        }
    }
    
    "4" {
        Write-Host ""
        Write-Host "僅查看狀態，未執行任何操作"
    }
    
    default {
        Write-Host ""
        Write-Host "✗ 無效的選項" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "操作完成！"
Write-Host "========================================"
Write-Host ""
Write-Host "當前 Git 狀態:"
git status
Write-Host ""
Write-Host "遠程倉庫:"
git remote -v 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  無遠程倉庫" -ForegroundColor Yellow
}

