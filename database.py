#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class BotDatabase:
    """Lớp quản lý dữ liệu bot (cảnh báo, thống kê, v.v.)"""
    
    def __init__(self, db_file: str = "bot_data.json"):
        self.db_file = db_file
        self.data = {
            "warnings": {},  # user_id: {"count": int, "reasons": [], "last_warning": datetime}
            "banned_users": {},  # user_id: {"reason": str, "date": datetime}
            "muted_users": {},  # user_id: {"until": datetime, "reason": str}
            "user_stats": {},  # user_id: {"messages": int, "join_date": datetime}
            "group_settings": {},  # group_id: {"welcome_enabled": bool, "rules": str}
            "message_stats": {"total": 0, "deleted": 0, "warnings_issued": 0}
        }
        self.load_data()
    
    def load_data(self):
        """Tải dữ liệu từ file JSON"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    self.data.update(loaded_data)
                print(f"✅ Đã tải dữ liệu từ {self.db_file}")
            except Exception as e:
                print(f"⚠️ Lỗi khi tải dữ liệu: {e}")
                self.create_backup()
        else:
            print(f"📁 Tạo file dữ liệu mới: {self.db_file}")
            self.save_data()
    
    def save_data(self):
        """Lưu dữ liệu vào file JSON"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"❌ Lỗi khi lưu dữ liệu: {e}")
    
    def create_backup(self):
        """Tạo file backup"""
        if os.path.exists(self.db_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.db_file}.backup_{timestamp}"
            try:
                import shutil
                shutil.copy2(self.db_file, backup_file)
                print(f"💾 Đã tạo backup: {backup_file}")
            except Exception as e:
                print(f"⚠️ Lỗi khi tạo backup: {e}")
    
    # === QUẢN LÝ CẢNH BÁO ===
    
    def add_warning(self, user_id: int, reason: str = "Không có lý do") -> int:
        """Thêm cảnh báo cho user"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.data["warnings"]:
            self.data["warnings"][user_id_str] = {
                "count": 0,
                "reasons": [],
                "last_warning": None
            }
        
        self.data["warnings"][user_id_str]["count"] += 1
        self.data["warnings"][user_id_str]["reasons"].append(reason)
        self.data["warnings"][user_id_str]["last_warning"] = datetime.now().isoformat()
        
        self.data["message_stats"]["warnings_issued"] += 1
        self.save_data()
        
        return self.data["warnings"][user_id_str]["count"]
    
    def get_warnings(self, user_id: int) -> Dict:
        """Lấy thông tin cảnh báo của user"""
        user_id_str = str(user_id)
        return self.data["warnings"].get(user_id_str, {
            "count": 0,
            "reasons": [],
            "last_warning": None
        })
    
    def clear_warnings(self, user_id: int):
        """Xóa tất cả cảnh báo của user"""
        user_id_str = str(user_id)
        if user_id_str in self.data["warnings"]:
            del self.data["warnings"][user_id_str]
            self.save_data()
    
    def get_all_warnings(self) -> Dict:
        """Lấy tất cả cảnh báo"""
        return self.data["warnings"]
    
    # === QUẢN LÝ BAN ===
    
    def add_ban(self, user_id: int, reason: str = "Vi phạm quy tắc"):
        """Thêm user vào danh sách ban"""
        user_id_str = str(user_id)
        self.data["banned_users"][user_id_str] = {
            "reason": reason,
            "date": datetime.now().isoformat()
        }
        self.save_data()
    
    def remove_ban(self, user_id: int):
        """Xóa user khỏi danh sách ban"""
        user_id_str = str(user_id)
        if user_id_str in self.data["banned_users"]:
            del self.data["banned_users"][user_id_str]
            self.save_data()
    
    def is_banned(self, user_id: int) -> bool:
        """Kiểm tra user có bị ban không"""
        user_id_str = str(user_id)
        return user_id_str in self.data["banned_users"]
    
    def get_ban_info(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin ban của user"""
        user_id_str = str(user_id)
        return self.data["banned_users"].get(user_id_str)
    
    # === QUẢN LÝ MUTE ===
    
    def add_mute(self, user_id: int, until: datetime, reason: str = "Mute"):
        """Thêm user vào danh sách mute"""
        user_id_str = str(user_id)
        self.data["muted_users"][user_id_str] = {
            "until": until.isoformat(),
            "reason": reason
        }
        self.save_data()
    
    def remove_mute(self, user_id: int):
        """Xóa user khỏi danh sách mute"""
        user_id_str = str(user_id)
        if user_id_str in self.data["muted_users"]:
            del self.data["muted_users"][user_id_str]
            self.save_data()
    
    def is_muted(self, user_id: int) -> bool:
        """Kiểm tra user có bị mute không"""
        user_id_str = str(user_id)
        if user_id_str not in self.data["muted_users"]:
            return False
        
        # Kiểm tra thời gian mute
        mute_info = self.data["muted_users"][user_id_str]
        mute_until = datetime.fromisoformat(mute_info["until"])
        
        if datetime.now() >= mute_until:
            self.remove_mute(user_id)
            return False
        
        return True
    
    def get_mute_info(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin mute của user"""
        user_id_str = str(user_id)
        return self.data["muted_users"].get(user_id_str)
    
    # === THỐNG KÊ USER ===
    
    def update_user_stats(self, user_id: int, message_count: int = 1):
        """Cập nhật thống kê user"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.data["user_stats"]:
            self.data["user_stats"][user_id_str] = {
                "messages": 0,
                "join_date": datetime.now().isoformat()
            }
        
        self.data["user_stats"][user_id_str]["messages"] += message_count
        self.save_data()
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Lấy thống kê user"""
        user_id_str = str(user_id)
        return self.data["user_stats"].get(user_id_str, {
            "messages": 0,
            "join_date": datetime.now().isoformat()
        })
    
    def get_top_users(self, limit: int = 10) -> List[tuple]:
        """Lấy top users theo số tin nhắn"""
        users = []
        for user_id_str, stats in self.data["user_stats"].items():
            users.append((user_id_str, stats["messages"]))
        
        return sorted(users, key=lambda x: x[1], reverse=True)[:limit]
    
    # === THỐNG KÊ CHUNG ===
    
    def increment_message_count(self):
        """Tăng số lượng tin nhắn"""
        self.data["message_stats"]["total"] += 1
        self.save_data()
    
    def increment_deleted_count(self):
        """Tăng số lượng tin nhắn bị xóa"""
        self.data["message_stats"]["deleted"] += 1
        self.save_data()
    
    def get_message_stats(self) -> Dict:
        """Lấy thống kê tin nhắn"""
        return self.data["message_stats"]
    
    def get_general_stats(self) -> Dict:
        """Lấy thống kê tổng quan"""
        return {
            "total_warnings": sum(w["count"] for w in self.data["warnings"].values()),
            "total_banned": len(self.data["banned_users"]),
            "total_muted": len(self.data["muted_users"]),
            "total_users": len(self.data["user_stats"]),
            "message_stats": self.data["message_stats"]
        }
    
    # === CÀI ĐẶT NHÓM ===
    
    def set_group_setting(self, group_id: int, key: str, value):
        """Thiết lập cài đặt nhóm"""
        group_id_str = str(group_id)
        
        if group_id_str not in self.data["group_settings"]:
            self.data["group_settings"][group_id_str] = {}
        
        self.data["group_settings"][group_id_str][key] = value
        self.save_data()
    
    def get_group_setting(self, group_id: int, key: str, default=None):
        """Lấy cài đặt nhóm"""
        group_id_str = str(group_id)
        return self.data["group_settings"].get(group_id_str, {}).get(key, default)
    
    def get_group_settings(self, group_id: int) -> Dict:
        """Lấy tất cả cài đặt nhóm"""
        group_id_str = str(group_id)
        return self.data["group_settings"].get(group_id_str, {})

# Singleton instance
db = BotDatabase()

# Convenience functions
def get_warnings(user_id: int) -> Dict:
    return db.get_warnings(user_id)

def add_warning(user_id: int, reason: str = "Không có lý do") -> int:
    return db.add_warning(user_id, reason)

def clear_warnings(user_id: int):
    db.clear_warnings(user_id)

def is_banned(user_id: int) -> bool:
    return db.is_banned(user_id)

def is_muted(user_id: int) -> bool:
    return db.is_muted(user_id) 