#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime

def create_sample_data():
    """Tạo dữ liệu mẫu để test dashboard"""
    
    # Tạo file channels.json mẫu
    sample_channels = {
        "@testchannel1": {
            "id": "@testchannel1",
            "name": "Kênh Test 1",
            "active": True,
            "added_date": "2024-01-15T10:30:00"
        },
        "@testchannel2": {
            "id": "@testchannel2", 
            "name": "Kênh Test 2",
            "active": True,
            "added_date": "2024-01-16T14:20:00"
        },
        "-1001234567890": {
            "id": "-1001234567890",
            "name": "Kênh Private",
            "active": False,
            "added_date": "2024-01-17T09:15:00"
        }
    }
    
    # Tạo file scheduled_posts.json mẫu
    sample_scheduled = {
        "schedule_20240120_100000_1": {
            "id": "schedule_20240120_100000_1",
            "content": "🔥 Chào buổi sáng! Hôm nay là ngày mới tuyệt vời!",
            "channels": ["@testchannel1", "@testchannel2"],
            "scheduled_time": "2024-01-20T10:00:00",
            "repeat_type": "daily",
            "status": "pending"
        },
        "schedule_20240121_150000_2": {
            "id": "schedule_20240121_150000_2", 
            "content": "🚀 Bài đăng quảng cáo sản phẩm mới!",
            "channels": ["@testchannel1"],
            "scheduled_time": "2024-01-21T15:00:00",
            "repeat_type": "none",
            "status": "pending"
        }
    }
    
    # Tạo file posts.json mẫu
    sample_posts = {
        "post_001": {
            "id": "post_001",
            "content": "⭐ Bài đăng đầu tiên từ dashboard",
            "channels": ["@testchannel1"],
            "sent_time": "2024-01-19T08:30:00",
            "status": "sent"
        }
    }
    
    # Lưu các file mẫu
    files_to_create = [
        ("channels.json", sample_channels),
        ("scheduled_posts.json", sample_scheduled),
        ("posts.json", sample_posts)
    ]
    
    for filename, data in files_to_create:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ Đã tạo file mẫu: {filename}")
        except Exception as e:
            print(f"❌ Lỗi khi tạo {filename}: {e}")
    
    print("\n🎉 Dữ liệu mẫu đã được tạo!")
    print("🌐 Bạn có thể chạy dashboard để xem dữ liệu:")
    print("   python start_dashboard.py")
    print("   hoặc")
    print("   python simple_dashboard.py")

if __name__ == '__main__':
    create_sample_data() 