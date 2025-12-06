#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART on FHIR Standalone 設置助手
幫助用戶配置和啟動 Standalone Launch
"""
import os
import sys
import re

# 設置 Windows 終端編碼
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def check_env_file():
    """檢查並更新 .env 文件"""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print("[錯誤] .env 文件不存在！")
        print("請先從模板創建: copy local.env.template .env")
        return False
    
    # 讀取 .env 文件
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查 SMART_CLIENT_ID
    client_id_match = re.search(r'SMART_CLIENT_ID=(.+)', content)
    if client_id_match:
        client_id = client_id_match.group(1).strip()
        if client_id == 'your-test-client-id' or client_id == 'your-client-id':
            print("=" * 60)
            print("[警告] 需要更新 SMART_CLIENT_ID")
            print("=" * 60)
            print("\n當前值: your-test-client-id (模板值)")
            print("\n請按照以下步驟獲取真實的 Client ID:")
            print("\n1. 訪問: https://launch.smarthealthit.org/register")
            print("2. 註冊新應用:")
            print("   - App Name: PRECISE-HBR")
            print("   - Redirect URI: http://localhost:8080/callback")
            print("   - Launch Type: Standalone Launch")
            print("   - Scopes: 選擇需要的權限")
            print("3. 複製生成的 Client ID")
            print("\n然後運行以下命令更新:")
            print("   python setup_smart_standalone.py --client-id YOUR_CLIENT_ID")
            print("\n或手動編輯 .env 文件")
            return False
        else:
            print(f"[OK] SMART_CLIENT_ID 已設置: {client_id[:20]}...")
    else:
        print("[警告] 未找到 SMART_CLIENT_ID 配置")
        return False
    
    # 檢查其他必要配置
    required_vars = {
        'SMART_REDIRECT_URI': 'http://localhost:8080/callback',
        'FLASK_SECRET_KEY': None
    }
    
    all_ok = True
    for var_name, default_value in required_vars.items():
        match = re.search(rf'{var_name}=(.+)', content)
        if not match or (default_value and match.group(1).strip() != default_value):
            if default_value:
                print(f"[警告] {var_name} 應設置為: {default_value}")
            else:
                print(f"[警告] {var_name} 未設置")
            all_ok = False
    
    if all_ok:
        print("[OK] 所有必要配置已設置")
    
    return all_ok

def update_client_id(client_id):
    """更新 .env 文件中的 SMART_CLIENT_ID"""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print("[錯誤] .env 文件不存在！")
        return False
    
    # 讀取文件
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新 SMART_CLIENT_ID
    updated_content = re.sub(
        r'SMART_CLIENT_ID=.+',
        f'SMART_CLIENT_ID={client_id}',
        content
    )
    
    # 寫回文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"[OK] 已更新 SMART_CLIENT_ID: {client_id}")
    return True

def main():
    """主函數"""
    print("=" * 60)
    print("SMART on FHIR Standalone 設置助手")
    print("=" * 60)
    print()
    
    # 檢查命令行參數
    if len(sys.argv) > 1:
        if sys.argv[1] == '--client-id' and len(sys.argv) > 2:
            client_id = sys.argv[2]
            if update_client_id(client_id):
                print("\n[OK] 配置已更新！現在可以啟動應用了。")
                print("\n運行: python start_app.py")
                return
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("用法:")
            print("  python setup_smart_standalone.py                    # 檢查配置")
            print("  python setup_smart_standalone.py --client-id ID    # 更新 Client ID")
            return
    
    # 檢查配置
    if check_env_file():
        print("\n" + "=" * 60)
        print("[OK] 配置檢查通過！")
        print("=" * 60)
        print("\n現在可以啟動應用了:")
        print("  python start_app.py")
        print("\n啟動後訪問:")
        print("  http://localhost:8080/standalone")
    else:
        print("\n" + "=" * 60)
        print("[錯誤] 配置需要更新")
        print("=" * 60)
        print("\n請按照上述說明更新配置後重試。")

if __name__ == '__main__':
    main()

