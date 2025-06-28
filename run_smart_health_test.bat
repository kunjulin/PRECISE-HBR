@echo off
echo ==============================================
echo FHIR 出血風險計算器 - SMART Health IT 測試
echo ==============================================
echo.
echo 正在啟動測試，這將需要幾分鐘時間...
echo 測試將從 SMART Health IT 獲取 30 個隨機患者
echo.

python test_smart_health_it.py

echo.
echo 測試完成！請檢查生成的報告文件。
pause 