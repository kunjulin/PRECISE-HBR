@echo off
chcp 65001 >nul
echo ============================================================
echo PRECISE-HBR 應用啟動腳本
echo ============================================================
echo.

REM 檢查命令行參數
if "%1"=="--network" goto network
if "%1"=="-n" goto network
if "%1"=="--local" goto local
if "%1"=="-l" goto local

REM 默認啟用網絡訪問
echo [信息] 默認啟用網絡訪問模式
echo [信息] 使用 --local 或 -l 參數可僅允許本地訪問
echo.
goto network

:network
echo [信息] 啟用網絡訪問模式（可通過 IP 地址訪問）
python start_app.py --network
goto end

:local
echo [信息] 僅允許本地訪問（localhost）
python start_app.py
goto end

:end
pause





