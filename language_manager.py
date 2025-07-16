#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from typing import Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Language(Enum):
    """Enum cho các ngôn ngữ được hỗ trợ"""
    VIETNAMESE = "vi"
    ENGLISH = "en" 
    CHINESE = "zh"

class LanguageManager:
    """Quản lý đa ngôn ngữ cho bot"""
    
    def __init__(self, default_language: Language = Language.VIETNAMESE):
        self.default_language = default_language
        self.current_language = default_language
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()
    
    def load_translations(self):
        """Tải tất cả bản dịch"""
        self.translations = {
            Language.VIETNAMESE.value: self._get_vietnamese_translations(),
            Language.ENGLISH.value: self._get_english_translations(),
            Language.CHINESE.value: self._get_chinese_translations()
        }
        logger.info(f"Đã tải bản dịch cho {len(self.translations)} ngôn ngữ")
    
    def set_language(self, language: Language):
        """Đặt ngôn ngữ hiện tại"""
        if language.value in self.translations:
            self.current_language = language
            logger.info(f"Đã chuyển sang ngôn ngữ: {language.value}")
        else:
            logger.warning(f"Ngôn ngữ {language.value} không được hỗ trợ")
    
    def get_text(self, key: str, language: Optional[Language] = None, **kwargs) -> str:
        """Lấy text theo ngôn ngữ"""
        lang = language.value if language else self.current_language.value
        
        # Fallback to default language if key not found
        if key not in self.translations.get(lang, {}):
            lang = self.default_language.value
        
        text = self.translations.get(lang, {}).get(key, key)
        
        # Format with kwargs if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"Error formatting text '{key}': {e}")
        
        return text
    
    def get_available_languages(self) -> Dict[str, str]:
        """Lấy danh sách ngôn ngữ có sẵn"""
        return {
            Language.VIETNAMESE.value: "🇻🇳 Tiếng Việt",
            Language.ENGLISH.value: "🇺🇸 English", 
            Language.CHINESE.value: "🇨🇳 中文"
        }
    
    def _get_vietnamese_translations(self) -> Dict[str, str]:
        """Bản dịch tiếng Việt"""
        return {
            # General
            "welcome": "🤖 **Chào mừng đến với Bot Đăng Bài Hàng Loạt!**\n\nBot giúp bạn đăng bài lên nhiều kênh Telegram cùng lúc một cách dễ dàng và hiệu quả.",
            "back": "🔙 Quay lại",
            "cancel": "❌ Hủy",
            "confirm": "✅ Xác nhận",
            "success": "✅ Thành công",
            "error": "❌ Lỗi",
            "loading": "⏳ Đang xử lý...",
            "done": "✅ Hoàn thành",
            
            # Menu items
            "main_menu": "📋 **Menu Chính**",
            "quick_post": "📢 Đăng bài ngay",
            "schedule_post": "⏰ Lên lịch đăng",
            "manage_channels": "📋 Quản lý kênh",
            "post_history": "📝 Lịch sử đăng",
            "settings": "⚙️ Cài đặt",
            "stats": "📊 Thống kê",
            "emoji_tools": "😊 Công cụ Emoji",
            
            # Settings
            "settings_title": "⚙️ **Cài đặt Bot**",
            "settings_bot": "🤖 Cài đặt Bot",
            "settings_scheduler": "⏰ Lịch đăng",
            "settings_notifications": "🔔 Thông báo",
            "settings_backup": "💾 Backup",
            "settings_security": "🔒 Bảo mật",
            "settings_interface": "🎨 Giao diện",
            "settings_advanced": "🔧 Nâng cao",
            "settings_export": "📤 Xuất/Nhập",
            
            # Channels
            "channels_title": "📋 **Quản lý Kênh**",
            "add_channel": "➕ Thêm kênh",
            "remove_channel": "🗑️ Xóa kênh", 
            "channel_stats": "📊 Thống kê kênh",
            "channel_search": "🔍 Tìm kiếm kênh",
            "bulk_actions": "⚡ Hành động hàng loạt",
            
            # Posts
            "create_post": "📝 Tạo bài đăng",
            "post_content": "Nội dung bài đăng",
            "post_type_text": "📝 Bài text",
            "post_type_photo": "📷 Bài có ảnh",
            "post_type_video": "🎬 Bài video",
            "post_type_file": "📄 Bài file",
            
            # Validation messages
            "invalid_input": "❌ Dữ liệu nhập không hợp lệ",
            "required_field": "⚠️ Trường này là bắt buộc",
            "invalid_range": "❌ Giá trị không nằm trong khoảng cho phép ({min}-{max})",
            "invalid_format": "❌ Định dạng không đúng",
            
            # Success messages
            "setting_updated": "✅ Đã cập nhật cài đặt {setting} = {value}",
            "channel_added": "✅ Đã thêm kênh thành công",
            "post_sent": "✅ Đã gửi bài đăng đến {count} kênh",
            "backup_created": "✅ Đã tạo backup thành công",
            
            # Error messages
            "permission_denied": "❌ Bạn không có quyền thực hiện hành động này",
            "channel_not_found": "❌ Không tìm thấy kênh",
            "post_failed": "❌ Không thể gửi bài đăng",
            "backup_failed": "❌ Không thể tạo backup",
            
            # Analytics
            "analytics_title": "📊 **Thống kê & Phân tích**",
            "total_posts": "Tổng bài đăng",
            "success_rate": "Tỷ lệ thành công",
            "active_channels": "Kênh hoạt động",
            "today_posts": "Bài đăng hôm nay",
            "weekly_stats": "Thống kê tuần",
            "monthly_stats": "Thống kê tháng",
        }
    
    def _get_english_translations(self) -> Dict[str, str]:
        """Bản dịch tiếng Anh"""
        return {
            # General
            "welcome": "🤖 **Welcome to Mass Post Bot!**\n\nThis bot helps you post to multiple Telegram channels simultaneously with ease and efficiency.",
            "back": "🔙 Back",
            "cancel": "❌ Cancel",
            "confirm": "✅ Confirm",
            "success": "✅ Success",
            "error": "❌ Error",
            "loading": "⏳ Processing...",
            "done": "✅ Done",
            
            # Menu items
            "main_menu": "📋 **Main Menu**",
            "quick_post": "📢 Quick Post",
            "schedule_post": "⏰ Schedule Post",
            "manage_channels": "📋 Manage Channels",
            "post_history": "📝 Post History",
            "settings": "⚙️ Settings",
            "stats": "📊 Statistics",
            "emoji_tools": "😊 Emoji Tools",
            
            # Settings
            "settings_title": "⚙️ **Bot Settings**",
            "settings_bot": "🤖 Bot Settings",
            "settings_scheduler": "⏰ Scheduler",
            "settings_notifications": "🔔 Notifications",
            "settings_backup": "💾 Backup",
            "settings_security": "🔒 Security",
            "settings_interface": "🎨 Interface",
            "settings_advanced": "🔧 Advanced",
            "settings_export": "📤 Export/Import",
            
            # Channels
            "channels_title": "📋 **Channel Management**",
            "add_channel": "➕ Add Channel",
            "remove_channel": "🗑️ Remove Channel",
            "channel_stats": "📊 Channel Stats",
            "channel_search": "🔍 Search Channels",
            "bulk_actions": "⚡ Bulk Actions",
            
            # Posts
            "create_post": "📝 Create Post",
            "post_content": "Post Content",
            "post_type_text": "📝 Text Post",
            "post_type_photo": "📷 Photo Post",
            "post_type_video": "🎬 Video Post",
            "post_type_file": "📄 File Post",
            
            # Validation messages
            "invalid_input": "❌ Invalid input data",
            "required_field": "⚠️ This field is required",
            "invalid_range": "❌ Value not in allowed range ({min}-{max})",
            "invalid_format": "❌ Invalid format",
            
            # Success messages
            "setting_updated": "✅ Updated setting {setting} = {value}",
            "channel_added": "✅ Channel added successfully",
            "post_sent": "✅ Post sent to {count} channels",
            "backup_created": "✅ Backup created successfully",
            
            # Error messages
            "permission_denied": "❌ You don't have permission to perform this action",
            "channel_not_found": "❌ Channel not found",
            "post_failed": "❌ Failed to send post",
            "backup_failed": "❌ Failed to create backup",
            
            # Analytics
            "analytics_title": "📊 **Analytics & Insights**",
            "total_posts": "Total Posts",
            "success_rate": "Success Rate",
            "active_channels": "Active Channels",
            "today_posts": "Today's Posts",
            "weekly_stats": "Weekly Stats",
            "monthly_stats": "Monthly Stats",
        }
    
    def _get_chinese_translations(self) -> Dict[str, str]:
        """Bản dịch tiếng Trung"""
        return {
            # General
            "welcome": "🤖 **欢迎使用群发机器人！**\n\n这个机器人可以帮助您轻松高效地同时向多个Telegram频道发布消息。",
            "back": "🔙 返回",
            "cancel": "❌ 取消",
            "confirm": "✅ 确认",
            "success": "✅ 成功",
            "error": "❌ 错误",
            "loading": "⏳ 处理中...",
            "done": "✅ 完成",
            
            # Menu items
            "main_menu": "📋 **主菜单**",
            "quick_post": "📢 快速发布",
            "schedule_post": "⏰ 定时发布",
            "manage_channels": "📋 管理频道",
            "post_history": "📝 发布历史",
            "settings": "⚙️ 设置",
            "stats": "📊 统计",
            "emoji_tools": "😊 表情工具",
            
            # Settings
            "settings_title": "⚙️ **机器人设置**",
            "settings_bot": "🤖 机器人设置",
            "settings_scheduler": "⏰ 调度器",
            "settings_notifications": "🔔 通知",
            "settings_backup": "💾 备份",
            "settings_security": "🔒 安全",
            "settings_interface": "🎨 界面",
            "settings_advanced": "🔧 高级",
            "settings_export": "📤 导出/导入",
            
            # Channels
            "channels_title": "📋 **频道管理**",
            "add_channel": "➕ 添加频道",
            "remove_channel": "🗑️ 删除频道",
            "channel_stats": "📊 频道统计",
            "channel_search": "🔍 搜索频道",
            "bulk_actions": "⚡ 批量操作",
            
            # Posts
            "create_post": "📝 创建帖子",
            "post_content": "帖子内容",
            "post_type_text": "📝 文字帖子",
            "post_type_photo": "📷 图片帖子",
            "post_type_video": "🎬 视频帖子",
            "post_type_file": "📄 文件帖子",
            
            # Validation messages
            "invalid_input": "❌ 输入数据无效",
            "required_field": "⚠️ 此字段为必填项",
            "invalid_range": "❌ 值不在允许范围内 ({min}-{max})",
            "invalid_format": "❌ 格式无效",
            
            # Success messages
            "setting_updated": "✅ 已更新设置 {setting} = {value}",
            "channel_added": "✅ 频道添加成功",
            "post_sent": "✅ 帖子已发送到 {count} 个频道",
            "backup_created": "✅ 备份创建成功",
            
            # Error messages
            "permission_denied": "❌ 您没有执行此操作的权限",
            "channel_not_found": "❌ 未找到频道",
            "post_failed": "❌ 发送帖子失败",
            "backup_failed": "❌ 创建备份失败",
            
            # Analytics
            "analytics_title": "📊 **分析与洞察**",
            "total_posts": "总帖子数",
            "success_rate": "成功率",
            "active_channels": "活跃频道",
            "today_posts": "今日帖子",
            "weekly_stats": "周统计",
            "monthly_stats": "月统计",
        }
    
    def save_user_language(self, user_id: int, language: Language):
        """Lưu ngôn ngữ của người dùng"""
        try:
            file_path = "user_languages.json"
            data = {}
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data[str(user_id)] = language.value
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Đã lưu ngôn ngữ {language.value} cho user {user_id}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu ngôn ngữ user: {e}")
    
    def get_user_language(self, user_id: int) -> Language:
        """Lấy ngôn ngữ của người dùng"""
        try:
            file_path = "user_languages.json"
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                user_lang = data.get(str(user_id))
                if user_lang:
                    for lang in Language:
                        if lang.value == user_lang:
                            return lang
                            
        except Exception as e:
            logger.error(f"Lỗi khi đọc ngôn ngữ user: {e}")
        
        return self.default_language

# Global instance
lang_manager = LanguageManager()

def get_text(key: str, language: Optional[Language] = None, **kwargs) -> str:
    """Shortcut function để lấy text"""
    return lang_manager.get_text(key, language, **kwargs)

def set_language(language: Language):
    """Shortcut function để đặt ngôn ngữ"""
    lang_manager.set_language(language) 