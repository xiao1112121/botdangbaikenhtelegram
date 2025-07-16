#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from telegram import Bot, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from telegram.constants import ParseMode
from telegram.error import TelegramError
import logging

logger = logging.getLogger(__name__)

# pyright: reportOptionalMemberAccess=false, reportAttributeAccessIssue=false, reportCallIssue=false, reportArgumentType=false, reportReturnType=false
class PostManager:
    """Quản lý bài đăng và gửi hàng loạt"""
    
    def __init__(self, db_file: str = "posts.json"):
        self.db_file = db_file
        self.posts = {}  # post_id: post_info
        self.load_posts()
    
    def load_posts(self):
        """Tải lịch sử bài đăng từ file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.posts = json.load(f)
                logger.info(f"Đã tải {len(self.posts)} bài đăng từ {self.db_file}")
            except Exception as e:
                logger.error(f"Lỗi khi tải bài đăng: {e}")
                self.posts = {}
        else:
            self.posts = {}
    
    def save_posts(self):
        """Lưu lịch sử bài đăng vào file"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.posts, f, ensure_ascii=False, indent=2)
            logger.info(f"Đã lưu {len(self.posts)} bài đăng vào {self.db_file}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu bài đăng: {e}")
    
    def create_post_id(self) -> str:
        """Tạo ID duy nhất cho bài đăng"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"post_{timestamp}_{len(self.posts)}"
    
    async def send_to_multiple_channels(
        self, 
        post_data: Dict[str, Any], 
        channels: List[Dict[str, Any]], 
        bot: Bot,
        delay_between_sends: int = 1
    ) -> Dict[str, Any]:
        """
        Gửi bài đăng đến nhiều kênh
        
        Args:
            post_data: Dữ liệu bài đăng
            channels: Danh sách kênh
            bot: Bot instance
            delay_between_sends: Delay giữa các lần gửi (giây)
            
        Returns:
            Dict chứa kết quả gửi
        """
        post_id = self.create_post_id()
        
        # Tạo bản ghi bài đăng
        post_record = {
            'id': post_id,
            'content': post_data.get('content', ''),
            'type': post_data.get('type', 'text'),
            'created_at': datetime.now().isoformat(),
            'channels': {},
            'total_channels': len(channels),
            'successful_sends': 0,
            'failed_sends': 0,
            'status': 'sending'
        }
        
        results = {
            'post_id': post_id,
            'total_channels': len(channels),
            'successful_sends': 0,
            'failed_sends': 0,
            'results': []
        }
        
        # Gửi đến từng kênh
        for i, channel in enumerate(channels):
            try:
                # Delay giữa các lần gửi
                if i > 0 and delay_between_sends > 0:
                    await asyncio.sleep(delay_between_sends)
                
                # Gửi bài đăng
                message = await self.send_to_channel(post_data, channel, bot)
                
                if message:
                    # Thành công
                    channel_result = {
                        'channel_id': channel['id'],
                        'channel_title': channel['title'],
                        'success': True,
                        'message_id': message.message_id,
                        'sent_at': datetime.now().isoformat()
                    }
                    results['successful_sends'] += 1
                    post_record['successful_sends'] += 1
                else:
                    # Thất bại
                    channel_result = {
                        'channel_id': channel['id'],
                        'channel_title': channel['title'],
                        'success': False,
                        'error': 'Không thể gửi tin nhắn',
                        'sent_at': datetime.now().isoformat()
                    }
                    results['failed_sends'] += 1
                    post_record['failed_sends'] += 1
                
                results['results'].append(channel_result)
                post_record['channels'][str(channel['id'])] = channel_result
                
            except Exception as e:
                logger.error(f"Lỗi khi gửi đến kênh {channel['title']}: {e}")
                
                channel_result = {
                    'channel_id': channel['id'],
                    'channel_title': channel['title'],
                    'success': False,
                    'error': str(e),
                    'sent_at': datetime.now().isoformat()
                }
                results['failed_sends'] += 1
                post_record['failed_sends'] += 1
                results['results'].append(channel_result)
                post_record['channels'][str(channel['id'])] = channel_result
        
        # Cập nhật trạng thái bài đăng
        post_record['status'] = 'completed'
        post_record['completed_at'] = datetime.now().isoformat()
        
        # Lưu bản ghi
        self.posts[post_id] = post_record
        self.save_posts()
        
        return results
    
    async def send_to_channel(self, post_data: Dict[str, Any], channel: Dict[str, Any], bot: Bot):
        """Gửi bài đăng đến một kênh"""
        try:
            channel_id = channel['id']
            post_type = post_data.get('type', 'text')
            
            if post_type == 'text':
                # Gửi tin nhắn text
                message = await bot.send_message(
                    chat_id=channel_id,
                    text=post_data['content'],
                    parse_mode=ParseMode.MARKDOWN if post_data.get('markdown', False) else None
                )
                
            elif post_type == 'photo':
                # Gửi hình ảnh
                message = await bot.send_photo(
                    chat_id=channel_id,
                    photo=post_data['media'],
                    caption=post_data.get('caption', ''),
                    parse_mode=ParseMode.MARKDOWN if post_data.get('markdown', False) else None
                )
                
            elif post_type == 'video':
                # Gửi video
                message = await bot.send_video(
                    chat_id=channel_id,
                    video=post_data['media'],
                    caption=post_data.get('caption', ''),
                    parse_mode=ParseMode.MARKDOWN if post_data.get('markdown', False) else None
                )

            elif post_type == 'document':
                # Gửi file
                message = await bot.send_document(
                    chat_id=channel_id,
                    document=post_data['media'],
                    caption=post_data.get('caption', ''),
                    parse_mode=ParseMode.MARKDOWN if post_data.get('markdown', False) else None
                )
                
            elif post_type == 'media_group':
                # Gửi nhóm media
                media_list = []
                for media_item in post_data['media_list']:
                    if media_item['type'] == 'photo':
                        media_list.append(InputMediaPhoto(media_item['file_id']))
                    elif media_item['type'] == 'video':
                        media_list.append(InputMediaVideo(media_item['file_id']))

                if media_list:
                    # Thêm caption vào media đầu tiên nếu có
                    caption = post_data.get('caption')
                    if caption and hasattr(media_list[0], 'caption'):
                        media_list[0].caption = caption

                    messages = await bot.send_media_group(
                        chat_id=channel_id,
                        media=media_list
                    )
                    message = messages[0] if messages else None
                else:
                    logger.warning(f"Loại bài đăng không hỗ trợ: {post_type}")
                    message = None
            
            return message
            
        except TelegramError as e:
            logger.error(f"Lỗi Telegram khi gửi đến kênh {channel['title']}: {e}")
            return None
        except Exception as e:
            logger.error(f"Lỗi không xác định khi gửi đến kênh {channel['title']}: {e}")
            return None
    
    async def get_post_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Lấy lịch sử bài đăng"""
        posts = list(self.posts.values())
        posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return posts[:limit]
    
    async def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin bài đăng theo ID"""
        return self.posts.get(post_id)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê bài đăng"""
        total_posts = len(self.posts)
        if total_posts == 0:
            return {
                'total_posts': 0,
                'successful_posts': 0,
                'failed_posts': 0,
                'success_rate': 0,
                'today_posts': 0,
                'today_success': 0,
                'top_channel': 'Chưa có dữ liệu'
            }
        
        successful_posts = sum(1 for post in self.posts.values() if post.get('successful_sends', 0) > 0)
        failed_posts = total_posts - successful_posts
        success_rate = (successful_posts / total_posts * 100) if total_posts > 0 else 0
        
        # Thống kê hôm nay
        today = datetime.now().date()
        today_posts = 0
        today_success = 0
        
        for post in self.posts.values():
            try:
                post_date = datetime.fromisoformat(post.get('created_at', '')).date()
                if post_date == today:
                    today_posts += 1
                    if post.get('successful_sends', 0) > 0:
                        today_success += 1
            except:
                pass
        
        # Tìm kênh được đăng nhiều nhất
        channel_stats = {}
        for post in self.posts.values():
            for channel_id, channel_result in post.get('channels', {}).items():
                if channel_result.get('success', False):
                    channel_title = channel_result.get('channel_title', 'Unknown')
                    channel_stats[channel_title] = channel_stats.get(channel_title, 0) + 1

        if channel_stats:
            # Lấy tên kênh có số lượng lớn nhất
            top_channel = max(channel_stats.items(), key=lambda item: item[1])[0]
        else:
            top_channel = 'Chưa có dữ liệu'

        return {
            'total_posts': total_posts,
            'successful_posts': successful_posts,
            'failed_posts': failed_posts,
            'success_rate': success_rate,
            'today_posts': today_posts,
            'today_success': today_success,
            'top_channel': top_channel,
            'pending_scheduled': 0,  # Sẽ được cập nhật từ scheduler
            'completed_scheduled': 0  # Sẽ được cập nhật từ scheduler
        }
    
    async def delete_post(self, post_id: str) -> bool:
        """Xóa bài đăng khỏi lịch sử"""
        if post_id in self.posts:
            del self.posts[post_id]
            self.save_posts()
            return True
        return False
    
    async def cleanup_old_posts(self, days: int = 30) -> int:
        """Dọn dẹp bài đăng cũ"""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        posts_to_delete = []
        
        for post_id, post in self.posts.items():
            try:
                post_date = datetime.fromisoformat(post.get('created_at', ''))
                if post_date < cutoff_date:
                    posts_to_delete.append(post_id)
            except:
                # Nếu không parse được date, coi như post cũ
                posts_to_delete.append(post_id)
        
        for post_id in posts_to_delete:
            del self.posts[post_id]
            deleted_count += 1
        
        if deleted_count > 0:
            self.save_posts()
        
        return deleted_count
    
    async def get_channel_post_stats(self, channel_id: str) -> Dict[str, Any]:
        """Lấy thống kê bài đăng của một kênh"""
        total_posts = 0
        successful_posts = 0
        failed_posts = 0
        
        for post in self.posts.values():
            channel_result = post.get('channels', {}).get(str(channel_id))
            if channel_result:
                total_posts += 1
                if channel_result.get('success', False):
                    successful_posts += 1
                else:
                    failed_posts += 1
        
        success_rate = (successful_posts / total_posts * 100) if total_posts > 0 else 0
        
        return {
            'total_posts': total_posts,
            'successful_posts': successful_posts,
            'failed_posts': failed_posts,
            'success_rate': success_rate
        }
    
    async def get_total_posts(self) -> int:
        """Trả về tổng số bài đã lưu"""
        return len(self.posts)

    async def count_posts(self) -> int:
        """Alias cho get_total_posts (giữ tương thích)"""
        return len(self.posts)
    
    def export_posts_to_json(self, filename: str = None) -> str:
        """Xuất dữ liệu bài đăng ra file JSON"""
        if filename is None:
            filename = f"posts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.posts, f, ensure_ascii=False, indent=2)
            return filename
        except Exception as e:
            logger.error(f"Lỗi khi xuất dữ liệu: {e}", exc_info=True)
            return None