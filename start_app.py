#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
應用啟動腳本
用於正常啟動 PRECISE-HBR 應用
"""
import os
import sys
import subprocess

def check_dependencies():
    """檢查必要的依賴是否已安裝"""
    # 包名和實際導入名的映射
    package_imports = {
        'flask': 'flask',
        'fhirclient': 'fhirclient',
        'flask_session': 'flask_session',
        'python-dotenv': 'dotenv',  # python-dotenv 包導入時使用 dotenv
        'PyJWT': 'jwt',  # PyJWT 包導入時使用 jwt
        'flask-cors': 'flask_cors',
        'flask-talisman': 'flask_talisman',
        'flask-wtf': 'flask_wtf'
    }
    
    missing = []
    for package_name, import_name in package_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print(f"[錯誤] 缺少以下依賴包: {', '.join(missing)}")
        print("請運行: pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """檢查 .env 文件是否存在"""
    if not os.path.exists('.env'):
        print("[警告] .env 文件不存在，正在從模板創建...")
        if os.path.exists('local.env.template'):
            import shutil
            shutil.copy('local.env.template', '.env')
            print("[成功] .env 文件已創建")
        else:
            print("[錯誤] local.env.template 文件不存在")
            return False
    return True

def start_app():
    """啟動應用"""
    print("=" * 60)
    print("PRECISE-HBR 應用啟動")
    print("=" * 60)
    
    # 檢查依賴
    if not check_dependencies():
        sys.exit(1)
    
    # 檢查環境文件
    if not check_env_file():
        sys.exit(1)
    
    # 設置環境變量
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = 'true'
    
    # 檢查是否允許網絡訪問（通過環境變量或命令行參數）
    allow_network = os.environ.get('ALLOW_NETWORK_ACCESS', 'false').lower() == 'true'
    if len(sys.argv) > 1 and sys.argv[1] in ['--network', '-n']:
        allow_network = True
    
    # 設置主機地址
    if allow_network:
        host = '0.0.0.0'  # 允許從所有網絡接口訪問
        os.environ['HOST'] = '0.0.0.0'
    else:
        host = '127.0.0.1'  # 僅本地訪問
        os.environ['HOST'] = '127.0.0.1'
    
    print("\n[信息] 正在啟動應用...")
    if allow_network:
        print("[信息] 應用將在 http://0.0.0.0:8080 上運行（允許網絡訪問）")
        print("\n⚠️  警告: 應用已啟用網絡訪問模式")
        print("   其他電腦可以通過您的 IP 地址訪問此應用")
    else:
        print("[信息] 應用將在 http://localhost:8080 上運行（僅本地訪問）")
        print("\n提示: 要允許網絡訪問，請使用: python start_app.py --network")
    
    print("\n本地訪問地址:")
    print("  - http://localhost:8080/")
    
    if allow_network:
        # 嘗試獲取本機 IP 地址
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            print("\n網絡訪問地址:")
            print(f"  - http://{local_ip}:8080/")
            print("\n其他電腦可以使用上述 IP 地址訪問此應用")
        except:
            print("\n無法自動檢測 IP 地址，請手動查看網絡配置")
    
    print("\n可用端點:")
    print("  - 主頁: http://localhost:8080/")
    print("  - 測試患者列表: http://localhost:8080/test-patients")
    print("  - 快速測試模式: http://localhost:8080/test-mode?patient_id=0322400A12345432900000000000000")
    print("  - Standalone Launch: http://localhost:8080/standalone")
    print("\n按 Ctrl+C 停止應用\n")
    print("-" * 60)
    
    # 導入並運行應用
    try:
        from APP import app
        app.run(host=host, port=8080, debug=True)
    except KeyboardInterrupt:
        print("\n\n[信息] 應用已停止")
    except Exception as e:
        print(f"\n[錯誤] 啟動失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    start_app()


