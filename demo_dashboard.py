#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import webbrowser
import time
import threading
from simple_dashboard import start_dashboard

def demo_dashboard():
    """Demo dashboard với tất cả trang"""
    print("🎮 Demo Dashboard - Bot Đăng Bài Hàng Loạt")
    print("=" * 60)
    
    # Khởi động dashboard trong thread riêng
    dashboard_thread = threading.Thread(target=start_dashboard, daemon=True)
    dashboard_thread.start()
    
    # Chờ dashboard khởi động
    time.sleep(2)
    
    print("🌐 Dashboard đã khởi động tại: http://localhost:8000")
    print()
    print("📋 Các trang có sẵn:")
    
    pages = [
        ("🏠 Trang chủ", "http://localhost:8000/", "Thống kê tổng quan, thông tin bot"),
        ("📢 Quản lý kênh", "http://localhost:8000/channels", "Thêm/xóa kênh Telegram"),
        ("✍️ Đăng bài", "http://localhost:8000/post", "Đăng bài lên nhiều kênh"),
        ("⏰ Lịch đăng", "http://localhost:8000/schedule", "Lên lịch đăng bài tự động"),
        ("😊 Công cụ Emoji", "http://localhost:8000/emoji", "Xử lý emoji, shortcode")
    ]
    
    for i, (name, url, desc) in enumerate(pages, 1):
        print(f"{i}. {name}")
        print(f"   URL: {url}")
        print(f"   Mô tả: {desc}")
        print()
    
    print("🎯 Hướng dẫn sử dụng:")
    print("1. Trang chủ: Xem thống kê tổng quan")
    print("2. Quản lý kênh: Thêm @username hoặc channel ID")
    print("3. Đăng bài: Soạn nội dung, chọn kênh, đăng ngay")
    print("4. Lịch đăng: Lên lịch với thời gian và tùy chọn lặp lại")
    print("5. Emoji: Xử lý shortcode [fire] → 🔥, emoji picker")
    print()
    
    print("🔧 Tính năng chính:")
    print("✅ Giao diện web trực quan")
    print("✅ Responsive design")
    print("✅ Emoji toolbar nhanh")
    print("✅ Shortcode processing")
    print("✅ Thống kê real-time")
    print("✅ Quản lý lịch đăng")
    print("✅ Multi-channel posting")
    print()
    
    print("🚀 Tự động mở browser...")
    try:
        webbrowser.open("http://localhost:8000")
        print("✅ Browser đã mở!")
    except:
        print("⚠️ Không thể mở browser tự động")
        print("   Vui lòng mở thủ công: http://localhost:8000")
    
    print()
    print("💡 Nhấn Ctrl+C để dừng dashboard")
    print("=" * 60)
    
    # Giữ chương trình chạy
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard demo đã dừng!")

if __name__ == "__main__":
    demo_dashboard() 