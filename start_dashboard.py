#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import threading
import time
from simple_dashboard import start_dashboard

def main():
    """Khởi động dashboard web cho bot"""
    print("🚀 Khởi động bảng điều khiển web...")
    print("=" * 50)
    
    # Kiểm tra các file cần thiết
    required_files = [
        'mass_post_bot.py',
        'channel_manager.py', 
        'post_manager.py',
        'scheduler.py',
        'config.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("⚠️  Cảnh báo: Một số file bot bị thiếu:")
        for file in missing_files:
            print(f"   - {file}")
        print("🔧 Dashboard vẫn hoạt động nhưng một số chức năng có thể bị hạn chế")
        print()
    
    print("🌐 Dashboard sẽ mở tại: http://localhost:8000")
    print("📋 Chức năng chính:")
    print("   • Quản lý kênh Telegram")
    print("   • Đăng bài hàng loạt")
    print("   • Lên lịch đăng bài")
    print("   • Công cụ xử lý emoji")
    print("   • Thống kê hoạt động")
    print()
    print("💡 Nhấn Ctrl+C để dừng dashboard")
    print("=" * 50)
    
    try:
        start_dashboard(port=8000)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard đã dừng!")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 