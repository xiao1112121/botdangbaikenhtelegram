#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import Config
import logging

logger = logging.getLogger(__name__)

class SettingsManager:
    """Quản lý cài đặt bot"""
    
    def __init__(self, settings_file: str = "bot_settings.json"):
        self.settings_file = settings_file
        self.settings = self._get_default_settings()
        self.load_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Cài đặt mặc định"""
        return {
            # Cài đặt bot
            "bot": {
                "delay_between_posts": Config.DEFAULT_DELAY_BETWEEN_POSTS,
                "max_channels_per_post": Config.MAX_CHANNELS_PER_POST,
                "default_parse_mode": Config.PARSE_MODE_DEFAULT,
                "disable_web_page_preview": Config.DISABLE_WEB_PAGE_PREVIEW,
                "default_notification": True,
                "default_protect_content": False,
                "rate_limit_enabled": True,
                "rate_limit_per_minute": 20
            },
            
            # Cài đặt scheduler
            "scheduler": {
                "check_interval": Config.SCHEDULER_CHECK_INTERVAL,
                "auto_cleanup_days": Config.AUTO_CLEANUP_DAYS,
                "max_scheduled_posts": 100,
                "enable_repeat_posts": True,
                "default_timezone": Config.TIMEZONE
            },
            
            # Cài đặt backup
            "backup": {
                "auto_backup_enabled": Config.ENABLE_AUTO_BACKUP,
                "backup_interval_hours": Config.BACKUP_INTERVAL_HOURS,
                "max_backup_files": 10,
                "backup_location": "./backups/",
                "include_media": False
            },
            
            # Cài đặt thông báo
            "notifications": {
                "admin_notifications": True,
                "post_success_notifications": True,
                "post_failure_notifications": True,
                "channel_status_notifications": True,
                "scheduler_notifications": True,
                "error_notifications": True
            },
            
            # Cài đặt bảo mật
            "security": {
                "admin_only_mode": True,
                "ban_duration_hours": 24,
                "max_warnings": 3,
                "auto_ban_on_max_warnings": True,
                "require_admin_approval": False,
                "log_all_actions": True
            },
            
            # Cài đặt giao diện
            "interface": {
                "language": "vi",
                "pagination_size": 5,
                "show_channel_stats": True,
                "show_post_previews": True,
                "emoji_shortcuts_enabled": True,
                "mini_app_enabled": True
            },
            
            # Cài đặt nâng cao
            "advanced": {
                "debug_mode": False,
                "verbose_logging": False,
                "log_file": Config.LOG_FILE,
                "log_level": Config.LOG_LEVEL,
                "api_timeout": 30,
                "retry_failed_posts": True,
                "max_retry_attempts": 3
            },
            
            # Metadata
            "meta": {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "update_count": 0
            }
        }
    
    def load_settings(self):
        """Tải cài đặt từ file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    
                # Merge với default settings để đảm bảo có đầy đủ keys
                self._merge_settings(self.settings, loaded_settings)
                logger.info(f"Đã tải cài đặt từ {self.settings_file}")
            except Exception as e:
                logger.error(f"Lỗi khi tải cài đặt: {e}")
                self.create_backup()
        else:
            logger.info("Tạo file cài đặt mới với giá trị mặc định")
            self.save_settings()
    
    def _merge_settings(self, default: Dict, loaded: Dict):
        """Merge settings loaded với default"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_settings(default[key], value)
                else:
                    default[key] = value
    
    def save_settings(self):
        """Lưu cài đặt vào file"""
        try:
            # Cập nhật metadata
            self.settings["meta"]["last_updated"] = datetime.now().isoformat()
            self.settings["meta"]["update_count"] += 1
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            logger.info(f"Đã lưu cài đặt vào {self.settings_file}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu cài đặt: {e}")
    
    def get_setting(self, category: str, key: str, default=None):
        """Lấy giá trị cài đặt"""
        return self.settings.get(category, {}).get(key, default)
    
    def set_setting(self, category: str, key: str, value: Any):
        """Đặt giá trị cài đặt"""
        if category not in self.settings:
            self.settings[category] = {}
        
        self.settings[category][key] = value
        self.save_settings()
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Lấy toàn bộ category"""
        return self.settings.get(category, {})
    
    def set_category(self, category: str, values: Dict[str, Any]):
        """Đặt toàn bộ category"""
        self.settings[category] = values
        self.save_settings()
    
    def reset_category(self, category: str):
        """Reset category về mặc định"""
        default_settings = self._get_default_settings()
        if category in default_settings:
            self.settings[category] = default_settings[category]
            self.save_settings()
    
    def reset_all_settings(self):
        """Reset tất cả cài đặt về mặc định"""
        self.settings = self._get_default_settings()
        self.save_settings()
    
    def create_backup(self):
        """Tạo backup cài đặt"""
        try:
            backup_name = f"settings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = os.path.join("backups", backup_name)
            
            # Tạo thư mục backup nếu chưa có
            os.makedirs("backups", exist_ok=True)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Đã tạo backup cài đặt: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Lỗi khi tạo backup: {e}")
            return None
    
    def restore_from_backup(self, backup_file: str) -> bool:
        """Khôi phục từ backup"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_settings = json.load(f)
            
            self.settings = backup_settings
            self.save_settings()
            logger.info(f"Đã khôi phục cài đặt từ {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi khôi phục từ backup: {e}")
            return False
    
    def export_settings(self, export_file: Optional[str] = None) -> Optional[str]:
        """Xuất cài đặt ra file"""
        if not export_file:
            export_file = f"settings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            logger.info(f"Đã xuất cài đặt ra {export_file}")
            return export_file
        except Exception as e:
            logger.error(f"Lỗi khi xuất cài đặt: {e}")
            return None
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Lấy tất cả cài đặt"""
        return self.settings.copy()
    
    def validate_settings(self) -> List[str]:
        """Kiểm tra tính hợp lệ của cài đặt"""
        errors = []
        
        # Kiểm tra delay
        delay = self.get_setting("bot", "delay_between_posts", 1)
        if delay < 1 or delay > 60:
            errors.append("Delay giữa các bài đăng phải từ 1-60 giây")
        
        # Kiểm tra số kênh tối đa
        max_channels = self.get_setting("bot", "max_channels_per_post", 10)
        if max_channels < 1 or max_channels > 200:
            errors.append("Số kênh tối đa phải từ 1-200")
        
        # Kiểm tra interval scheduler
        interval = self.get_setting("scheduler", "check_interval", 30)
        if interval < 10 or interval > 3600:
            errors.append("Interval check scheduler phải từ 10-3600 giây")
        
        return errors 