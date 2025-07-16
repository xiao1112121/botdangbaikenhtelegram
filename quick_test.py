#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

def quick_test():
    """Test nhanh dashboard"""
    
    print("🚀 Kiểm tra Dashboard...")
    
    # Kiểm tra file cần thiết
    files_to_check = [
        'simple_dashboard.py',
        'start_dashboard.py',
        'channels.json',
        'scheduled_posts.json',
        'posts.json'
    ]
    
    missing_files = []
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (thiếu)")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Thiếu {len(missing_files)} file")
    else:
        print("\n✅ Tất cả file đã sẵn sàng!")
    
    print("\n🌐 Để chạy dashboard:")
    print("   python start_dashboard.py")
    print("   Hoặc: python simple_dashboard.py")
    print("   Sau đó mở: http://localhost:8000")
    
    print("\n📋 Chức năng dashboard:")
    print("   • Trang chủ với thống kê")
    print("   • Quản lý kênh Telegram")
    print("   • Đăng bài hàng loạt")
    print("   • Công cụ emoji")
    print("   • Lên lịch đăng bài")
    
    return len(missing_files) == 0

if __name__ == '__main__':
    success = quick_test()
    if success:
        print("\n🎉 Dashboard sẵn sàng hoạt động!")
    else:
        print("\n❌ Cần khắc phục lỗi trước khi chạy dashboard") 