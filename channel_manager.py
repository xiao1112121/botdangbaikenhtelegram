#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from telegram import Bot
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError
import logging

logger = logging.getLogger(__name__)

# pyright: reportOptionalMemberAccess=false, reportCallIssue=false, reportArgumentType=false
class ChannelManager:
    """Quản lý danh sách kênh Telegram"""
    
    def __init__(self, db_file: str = "channels.json"):
        self.db_file = db_file
        self.channels = {}  # channel_id: channel_info
        self.load_channels()
    
    def load_channels(self):
        """Tải danh sách kênh từ file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.channels = json.load(f)
                logger.info(f"Đã tải {len(self.channels)} kênh từ {self.db_file}")
            except Exception as e:
                logger.error(f"Lỗi khi tải kênh: {e}")
                self.channels = {}
        else:
            self.channels = {}
    
    def save_channels(self):
        """Lưu danh sách kênh vào file"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.channels, f, ensure_ascii=False, indent=2)
            logger.info(f"Đã lưu {len(self.channels)} kênh vào {self.db_file}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu kênh: {e}")
    
    async def add_channel(self, channel_input: str, bot: Bot) -> Dict[str, Any]:
        """
        Thêm kênh mới
        
        Args:
            channel_input: @username hoặc channel_id
            bot: Bot instance để kiểm tra quyền
            
        Returns:
            Dict chứa thông tin kết quả
        """
        try:
            # Lấy thông tin chat
            try:
                if channel_input.startswith('@'):
                    # Pyright khó nhận dạng signature của get_chat khi truyền str, thêm ignore
                    chat = await bot.get_chat(channel_input)  # type: ignore[arg-type]
                else:
                    # Thử parse ID
                    chat_id = int(channel_input)
                    chat = await bot.get_chat(chat_id)  # type: ignore[arg-type]
            except (ValueError, TypeError):
                return {
                    'success': False, 
                    'error': 'ID kênh không hợp lệ'
                }
            except TelegramError as e:
                return {
                    'success': False,
                    'error': f'Lỗi khi lấy thông tin kênh: {str(e)}'
                }
            
            # Kiểm tra loại chat
            if chat.type not in ['channel', 'supergroup']:
                return {
                    'success': False,
                    'error': 'Chỉ hỗ trợ kênh (channel) hoặc supergroup'
                }
            
            # Kiểm tra quyền admin của bot
            try:
                me = await bot.get_me()
                bot_member = await bot.get_chat_member(chat.id, me.id)
                if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    return {
                        'success': False,
                        'error': 'Bot không có quyền admin trong kênh này'
                    }
                
                # Kiểm tra quyền đăng bài
                if hasattr(bot_member, 'can_post_messages') and not bot_member.can_post_messages:
                    return {
                        'success': False,
                        'error': 'Bot không có quyền đăng bài trong kênh này'
                    }
                    
            except TelegramError as e:
                return {
                    'success': False,
                    'error': f'Không thể kiểm tra quyền: {str(e)}'
                }
            
            # Kiểm tra kênh đã tồn tại chưa
            if str(chat.id) in self.channels:
                return {
                    'success': False,
                    'error': 'Kênh đã được thêm rồi'
                }
            
            # Thêm kênh vào danh sách
            channel_info = {
                'id': chat.id,
                'title': chat.title,
                'username': chat.username or '',
                'type': chat.type,
                'active': True,
                'added_date': datetime.now().isoformat(),
                'post_count': 0,
                'success_count': 0,
                'fail_count': 0,
                'last_post': None
            }
            
            self.channels[str(chat.id)] = channel_info
            self.save_channels()
            
            return {
                'success': True,
                'channel': channel_info,
                'channel_name': channel_info['title'],
                'channel_id': channel_info['id']
            }
            
        except TelegramError as e:
            return {
                'success': False,
                'error': f'Lỗi Telegram: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Lỗi không xác định: {str(e)}'
            }
    
    async def remove_channel(self, channel_id: str) -> bool:
        """Xóa kênh khỏi danh sách (hỗ trợ id dạng str hoặc int)"""
        # Tìm kênh theo nhiều cách
        channel_key_to_remove = None
        
        # 1. Thử tìm theo key trực tiếp
        key = str(channel_id)
        if key in self.channels:
            channel_key_to_remove = key
        
        # 2. Thử tìm theo int key (cho JSON cũ)
        if not channel_key_to_remove:
            try:
                int_key = int(channel_id)
                if int_key in self.channels:
                    channel_key_to_remove = int_key
            except ValueError:
                pass
        
        # 3. Thử tìm theo id field trong data
        if not channel_key_to_remove:
            for key, channel_data in self.channels.items():
                if str(channel_data.get('id')) == str(channel_id):
                    channel_key_to_remove = key
                    break
        
        # Xóa kênh nếu tìm thấy
        if channel_key_to_remove is not None:
            del self.channels[channel_key_to_remove]
            self.save_channels()
            return True
        
        return False
    
    async def get_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin kênh"""
        # 1. Thử tìm theo key trực tiếp
        if channel_id in self.channels:
            return self.channels[channel_id]
        
        # 2. Thử tìm theo int key
        try:
            int_key = int(channel_id)
            if int_key in self.channels:
                return self.channels[int_key]
        except ValueError:
            pass
        
        # 3. Thử tìm theo id field trong data
        for channel_data in self.channels.values():
            if str(channel_data.get('id')) == str(channel_id):
                return channel_data
        
        return None
    
    async def get_all_channels(self) -> List[Dict[str, Any]]:
        """Lấy tất cả kênh"""
        return list(self.channels.values())

    # Synchronous wrapper cho dashboard
    def get_all_channels_sync(self) -> List[Dict[str, Any]]:
        """Trả về danh sách kênh (sync)"""
        return list(self.channels.values())

    def get_active_channels_sync(self) -> List[Dict[str, Any]]:
        """Trả về kênh active (sync)"""
        return [c for c in self.channels.values() if c.get('active', True)]
    
    async def get_active_channels(self) -> List[Dict[str, Any]]:
        """Lấy các kênh đang hoạt động"""
        return [channel for channel in self.channels.values() if channel.get('active', True)]
    
    async def toggle_channel_status(self, channel_id: str) -> bool:
        """Bật/tắt trạng thái kênh"""
        if channel_id in self.channels:
            self.channels[channel_id]['active'] = not self.channels[channel_id].get('active', True)
            self.save_channels()
            return True
        return False
    
    async def update_channel_stats(self, channel_id: str, success: bool = True):
        """Cập nhật thống kê kênh"""
        if channel_id in self.channels:
            self.channels[channel_id]['post_count'] += 1
            self.channels[channel_id]['last_post'] = datetime.now().isoformat()
            
            if success:
                self.channels[channel_id]['success_count'] += 1
            else:
                self.channels[channel_id]['fail_count'] += 1
            
            self.save_channels()
    
    async def check_channel_permissions(self, channel_id: str, bot: Bot) -> Dict[str, Any]:
        """Kiểm tra quyền bot trong kênh"""
        try:
            # Convert channel_id to int if it's a string
            chat_id = int(channel_id) if isinstance(channel_id, str) else channel_id
            bot_member = await bot.get_chat_member(chat_id, (await bot.get_me()).id)  # type: ignore[arg-type]
            
            return {
                'is_admin': bot_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER],
                'can_post': getattr(bot_member, 'can_post_messages', False),
                'can_edit': getattr(bot_member, 'can_edit_messages', False),
                'can_delete': getattr(bot_member, 'can_delete_messages', False),
                'status': bot_member.status
            }
        except TelegramError as e:
            return {
                'error': str(e),
                'is_admin': False,
                'can_post': False
            }
    
    async def get_channel_stats(self) -> Dict[str, Any]:
        """Lấy thống kê tổng quan về kênh"""
        total_channels = len(self.channels)
        active_channels = len(await self.get_active_channels())
        
        total_posts = sum(channel.get('post_count', 0) for channel in self.channels.values())
        total_success = sum(channel.get('success_count', 0) for channel in self.channels.values())
        total_fail = sum(channel.get('fail_count', 0) for channel in self.channels.values())
        
        success_rate = (total_success / total_posts * 100) if total_posts > 0 else 0
        
        # Tìm kênh hoạt động nhất
        top_channel = None
        max_posts = 0
        for channel in self.channels.values():
            if channel.get('post_count', 0) > max_posts:
                max_posts = channel.get('post_count', 0)
                top_channel = channel
        
        return {
            'total_channels': total_channels,
            'active_channels': active_channels,
            'inactive_channels': total_channels - active_channels,
            'total_posts': total_posts,
            'total_success': total_success,
            'total_fail': total_fail,
            'success_rate': success_rate,
            'top_channel': top_channel
        }
    
    async def cleanup_inactive_channels(self) -> int:
        """Dọn dẹp kênh không hoạt động"""
        removed_count = 0
        channels_to_remove = []
        
        for channel_id, channel in self.channels.items():
            if not channel.get('active', True) and channel.get('post_count', 0) == 0:
                channels_to_remove.append(channel_id)
        
        for channel_id in channels_to_remove:
            del self.channels[channel_id]
            removed_count += 1
        
        if removed_count > 0:
            self.save_channels()
        
        return removed_count
    
    def get_channel_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Tìm kênh theo username"""
        username = username.replace('@', '')
        for channel in self.channels.values():
            if channel.get('username', '').lower() == username.lower():
                return channel
        return None
    
    def search_channels(self, query: str) -> List[Dict[str, Any]]:
        """Tìm kiếm kênh theo tên hoặc username"""
        query = query.lower()
        results = []
        
        for channel in self.channels.values():
            if (query in channel.get('title', '').lower() or 
                query in channel.get('username', '').lower()):
                results.append(channel)
        
        return results
    
    def export_channels_to_json(self) -> str:
        """Xuất danh sách kênh ra JSON string"""
        import json
        from datetime import datetime
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_channels': len(self.channels),
            'channels': self.channels
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    def import_channels_from_json(self, json_data: str) -> Dict[str, Any]:
        """Nhập danh sách kênh từ JSON string"""
        try:
            import json
            data = json.loads(json_data)
            
            if 'channels' not in data:
                return {'success': False, 'error': 'Dữ liệu không hợp lệ - thiếu trường channels'}
            
            imported_channels = data['channels']
            added_count = 0
            skipped_count = 0
            
            for channel_id, channel_info in imported_channels.items():
                if channel_id not in self.channels:
                    self.channels[channel_id] = channel_info
                    added_count += 1
                else:
                    skipped_count += 1
            
            if added_count > 0:
                self.save_channels()
            
            return {
                'success': True,
                'added': added_count,
                'skipped': skipped_count,
                'total': len(imported_channels)
            }
            
        except json.JSONDecodeError:
            return {'success': False, 'error': 'Dữ liệu JSON không hợp lệ'}
        except Exception as e:
            return {'success': False, 'error': f'Lỗi: {str(e)}'}
    
    def create_backup(self, backup_name: str = None) -> str:
        """Tạo backup của danh sách kênh"""
        from datetime import datetime
        import os
        
        if not backup_name:
            backup_name = f"channels_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        backup_path = f"backups/{backup_name}"
        
        # Tạo thư mục backup nếu chưa có
        os.makedirs("backups", exist_ok=True)
        
        backup_data = self.export_channels_to_json()
        
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(backup_data)
            return backup_path
        except Exception as e:
            raise Exception(f"Không thể tạo backup: {str(e)}")
    
    def list_backups(self) -> List[str]:
        """Liệt kê các file backup có sẵn"""
        import os
        backup_dir = "backups"
        
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for file in os.listdir(backup_dir):
            if file.endswith('.json') and 'channels_backup' in file:
                backups.append(file)
        
        return sorted(backups, reverse=True)  # Mới nhất trước
    
    def restore_from_backup(self, backup_file: str) -> Dict[str, Any]:
        """Khôi phục từ backup file"""
        import os
        
        backup_path = f"backups/{backup_file}"
        
        if not os.path.exists(backup_path):
            return {'success': False, 'error': 'File backup không tồn tại'}
        
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = f.read()
            
            result = self.import_channels_from_json(backup_data)
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'Lỗi đọc backup: {str(e)}'}
    
    async def validate_all_channels(self, bot) -> Dict[str, Any]:
        """Validate tất cả kênh và trả về báo cáo"""
        report = {
            'total': len(self.channels),
            'valid': 0,
            'invalid': 0,
            'no_permission': 0,
            'details': []
        }
        
        for channel_id, channel_info in self.channels.items():
            try:
                # Kiểm tra quyền
                permissions = await self.check_channel_permissions(channel_id, bot)
                
                if 'error' in permissions:
                    report['invalid'] += 1
                    report['details'].append({
                        'id': channel_id,
                        'title': channel_info.get('title', 'Unknown'),
                        'status': 'invalid',
                        'error': permissions['error']
                    })
                elif not permissions['is_admin'] or not permissions.get('can_post', False):
                    report['no_permission'] += 1
                    report['details'].append({
                        'id': channel_id,
                        'title': channel_info.get('title', 'Unknown'),
                        'status': 'no_permission',
                        'permissions': permissions
                    })
                else:
                    report['valid'] += 1
                    report['details'].append({
                        'id': channel_id,
                        'title': channel_info.get('title', 'Unknown'),
                        'status': 'valid',
                        'permissions': permissions
                    })
                    
            except Exception as e:
                report['invalid'] += 1
                report['details'].append({
                    'id': channel_id,
                    'title': channel_info.get('title', 'Unknown'),
                    'status': 'error',
                    'error': str(e)
                })
        
        return report 