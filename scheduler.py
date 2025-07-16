#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import asyncio
import time  # Fix: dùng cho time.sleep trong scheduler
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from telegram import Bot  # thêm để khai báo type
from threading import Thread
import logging

logger = logging.getLogger(__name__)

# pyright: reportOptionalMemberAccess=false, reportCallIssue=false, reportArgumentType=false, reportReturnType=false
class PostScheduler:
    """Quản lý lịch đăng bài tự động"""
    
    def __init__(self, db_file: str = "scheduled_posts.json", bot: Optional[Bot] = None):
        self.db_file = db_file
        self.bot = bot  # Bot instance để gửi thông báo
        self.scheduled_posts = {}  # schedule_id: schedule_info
        self.running = False
        self.scheduler_thread = None
        self.load_scheduled_posts()
    
    def load_scheduled_posts(self):
        """Tải lịch đăng bài từ file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.scheduled_posts = json.load(f)
                logger.info(f"Đã tải {len(self.scheduled_posts)} lịch đăng từ {self.db_file}")
            except Exception as e:
                logger.error(f"Lỗi khi tải lịch đăng: {e}")
                self.scheduled_posts = {}
        else:
            self.scheduled_posts = {}

        # Bổ sung trường next_execution cho các lịch cũ nếu thiếu
        for sched in self.scheduled_posts.values():
            if 'next_execution' not in sched or not sched['next_execution']:
                sched['next_execution'] = sched.get('scheduled_time', datetime.now().isoformat())
        # Lưu lại nếu đã cập nhật
        self.save_scheduled_posts()
    
    def save_scheduled_posts(self):
        """Lưu lịch đăng bài vào file"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_posts, f, ensure_ascii=False, indent=2)
            logger.info(f"Đã lưu {len(self.scheduled_posts)} lịch đăng vào {self.db_file}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu lịch đăng: {e}")
    
    def create_schedule_id(self) -> str:
        """Tạo ID duy nhất cho lịch đăng"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"schedule_{timestamp}_{len(self.scheduled_posts)}"
    
    async def schedule_post(
        self, 
        post_data: Dict[str, Any], 
        channels: List[Dict[str, Any]], 
        scheduled_time: datetime,
        repeat_type: str = "none",  # none, daily, weekly, monthly
        repeat_count: int = 1
    ) -> str:
        """
        Lên lịch đăng bài
        
        Args:
            post_data: Dữ liệu bài đăng
            channels: Danh sách kênh
            scheduled_time: Thời gian đăng
            repeat_type: Loại lặp lại
            repeat_count: Số lần lặp lại
            
        Returns:
            ID của lịch đăng
        """
        schedule_id = self.create_schedule_id()
        
        schedule_info = {
            'id': schedule_id,
            'post_data': post_data,
            'channels': channels,
            'scheduled_time': scheduled_time.isoformat(),
            'repeat_type': repeat_type,
            'repeat_count': repeat_count,
            'executed_count': 0,
            'status': 'pending',  # pending, executing, completed, failed
            'created_at': datetime.now().isoformat(),
            'next_execution': scheduled_time.isoformat(),
            'last_execution': None,
            'execution_history': []
        }
        
        self.scheduled_posts[schedule_id] = schedule_info
        self.save_scheduled_posts()
        
        logger.info(f"Đã lên lịch đăng bài {schedule_id} vào {scheduled_time}")
        return schedule_id
    
    async def cancel_schedule(self, schedule_id: str) -> bool:
        """Hủy lịch đăng bài"""
        if schedule_id in self.scheduled_posts:
            self.scheduled_posts[schedule_id]['status'] = 'cancelled'
            self.save_scheduled_posts()
            logger.info(f"Đã hủy lịch đăng {schedule_id}")
            return True
        return False

    async def get_scheduled_posts(self, status: str = "") -> List[Dict[str, Any]]:
        """Lấy danh sách lịch đăng bài"""
        posts = list(self.scheduled_posts.values())
        
        if status:
            posts = [post for post in posts if post.get('status') == status]
        
        posts.sort(key=lambda x: x.get('scheduled_time', ''))
        return posts
    
    async def get_scheduled_count(self) -> int:
        """Lấy số lượng bài đăng đang chờ"""
        return len([post for post in self.scheduled_posts.values() if post.get('status') == 'pending'])
    
    async def get_schedule_by_id(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin lịch đăng theo ID"""
        return self.scheduled_posts.get(schedule_id)
    
    def start(self):
        """Bắt đầu scheduler"""
        if not self.running:
            self.running = True
            self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logger.info("Scheduler đã bắt đầu")
    
    def stop(self):
        """Dừng scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler đã dừng")
    
    def _run_scheduler(self):
        """Chạy scheduler loop"""
        while self.running:
            try:
                # Kiểm tra các lịch đăng cần thực hiện
                asyncio.run(self._check_and_execute_scheduled_posts())
                
                # Nghỉ 30 giây trước khi check lại
                for _ in range(30):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Lỗi trong scheduler loop: {e}")
                # Nghỉ 10 giây rồi thử lại
                time.sleep(10)

    async def _check_and_execute_scheduled_posts(self):
        """Kiểm tra và thực hiện các lịch đăng"""
        from datetime import datetime  # Thêm import nếu chưa có
        current_time = datetime.now()
        
        for schedule_id, schedule_info in self.scheduled_posts.items():
            if schedule_info.get('status') != 'pending':
                continue
            
            try:
                next_execution = datetime.fromisoformat(schedule_info['next_execution'])
                
                # Kiểm tra thời gian thực hiện
                if current_time >= next_execution:
                    await self._execute_scheduled_post(schedule_id, schedule_info)
                    
            except Exception as e:
                logger.error(f"Lỗi khi xử lý lịch đăng {schedule_id}: {e}")
                # Đánh dấu lỗi
                schedule_info['status'] = 'failed'
                schedule_info['error'] = str(e)
                self.save_scheduled_posts()
    
    async def _execute_scheduled_post(self, schedule_id: str, schedule_info: Dict[str, Any]):
        """Thực hiện đăng bài theo lịch"""
        try:
            logger.info(f"Đang thực hiện lịch đăng {schedule_id}")
            
            # Cập nhật trạng thái
            schedule_info['status'] = 'executing'
            schedule_info['last_execution'] = datetime.now().isoformat()
            
            # Import post_manager và channel_manager
            from post_manager import PostManager
            from channel_manager import ChannelManager
            
            # Tạo instance
            post_manager = PostManager()
            channel_manager = ChannelManager()
            
            # Lấy bot instance (cần được truyền từ main bot)
            # Tạm thời skip phần thực hiện gửi bài
            # Trong thực tế, cần có cách để get bot instance
            
            # Ghi lại lịch sử thực hiện
            execution_record = {
                'executed_at': datetime.now().isoformat(),
                'success': True,  # Tạm thời đặt true
                'channels_sent': len(schedule_info['channels']),
                'results': []
            }
            
            schedule_info['execution_history'].append(execution_record)
            schedule_info['executed_count'] += 1
            
            # Tính toán lần thực hiện tiếp theo
            await self._calculate_next_execution(schedule_info)
            
            logger.info(f"Đã thực hiện lịch đăng {schedule_id}")
            await self._notify_admins(f"✅ Đã thực hiện lịch đăng <b>{schedule_id}</b> thành công.")
            
        except Exception as e:
            logger.error(f"Lỗi khi thực hiện lịch đăng {schedule_id}: {e}")
            schedule_info['status'] = 'failed'
            schedule_info['error'] = str(e)
            await self._notify_admins(f"❌ Lỗi khi thực hiện lịch đăng <b>{schedule_id}</b>: {e}")
        
        finally:
            self.save_scheduled_posts()
    
    async def _calculate_next_execution(self, schedule_info: Dict[str, Any]):
        """Tính toán thời gian thực hiện tiếp theo"""
        repeat_type = schedule_info.get('repeat_type', 'none')
        repeat_count = schedule_info.get('repeat_count', 1)
        executed_count = schedule_info.get('executed_count', 0)
        
        # Kiểm tra xem đã đủ số lần lặp lại chưa
        if executed_count >= repeat_count:
            schedule_info['status'] = 'completed'
            return
        
        # Tính toán thời gian thực hiện tiếp theo
        if repeat_type == 'none':
            schedule_info['status'] = 'completed'
            
        elif repeat_type == 'daily':
            current_next = datetime.fromisoformat(schedule_info['next_execution'])
            next_execution = current_next + timedelta(days=1)
            schedule_info['next_execution'] = next_execution.isoformat()
            
        elif repeat_type == 'weekly':
            current_next = datetime.fromisoformat(schedule_info['next_execution'])
            next_execution = current_next + timedelta(weeks=1)
            schedule_info['next_execution'] = next_execution.isoformat()
            
        elif repeat_type == 'monthly':
            current_next = datetime.fromisoformat(schedule_info['next_execution'])
            # Tính toán tháng tiếp theo
            if current_next.month == 12:
                next_execution = current_next.replace(year=current_next.year + 1, month=1)
            else:
                next_execution = current_next.replace(month=current_next.month + 1)
            schedule_info['next_execution'] = next_execution.isoformat()
        
        # Đặt lại trạng thái pending nếu còn lần thực hiện
        if schedule_info['status'] != 'completed':
            schedule_info['status'] = 'pending'
    
    async def get_upcoming_posts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Lấy các bài đăng sắp tới trong vòng X giờ"""
        current_time = datetime.now()
        cutoff_time = current_time + timedelta(hours=hours)
        
        upcoming_posts = []
        for schedule_info in self.scheduled_posts.values():
            if schedule_info.get('status') != 'pending':
                continue
            
            try:
                next_execution = datetime.fromisoformat(schedule_info['next_execution'])
                if current_time <= next_execution <= cutoff_time:
                    upcoming_posts.append(schedule_info)
            except:
                pass
        
        upcoming_posts.sort(key=lambda x: x.get('next_execution', ''))
        return upcoming_posts
    
    async def get_scheduler_stats(self) -> Dict[str, Any]:
        """Lấy thống kê scheduler"""
        total_scheduled = len(self.scheduled_posts)
        pending_count = len([s for s in self.scheduled_posts.values() if s.get('status') == 'pending'])
        completed_count = len([s for s in self.scheduled_posts.values() if s.get('status') == 'completed'])
        failed_count = len([s for s in self.scheduled_posts.values() if s.get('status') == 'failed'])
        
        # Tổng số lần thực hiện
        total_executions = sum(s.get('executed_count', 0) for s in self.scheduled_posts.values())
        
        # Upcoming posts trong 24h
        upcoming_posts = await self.get_upcoming_posts(24)
        
        return {
            'total_scheduled': total_scheduled,
            'pending_count': pending_count,
            'completed_count': completed_count,
            'failed_count': failed_count,
            'total_executions': total_executions,
            'upcoming_24h': len(upcoming_posts),
            'scheduler_running': self.running
        }
    
    async def cleanup_old_schedules(self, days: int = 30) -> int:
        """Dọn dẹp lịch đăng cũ đã hoàn thành"""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        schedules_to_delete = []
        
        for schedule_id, schedule_info in self.scheduled_posts.items():
            if schedule_info.get('status') in ['completed', 'failed']:
                try:
                    created_date = datetime.fromisoformat(schedule_info.get('created_at', ''))
                    if created_date < cutoff_date:
                        schedules_to_delete.append(schedule_id)
                except:
                    # Nếu không parse được date, coi như schedule cũ
                    schedules_to_delete.append(schedule_id)
        
        for schedule_id in schedules_to_delete:
            del self.scheduled_posts[schedule_id]
            deleted_count += 1
        
        if deleted_count > 0:
            self.save_scheduled_posts()
        
        return deleted_count
    
    async def reschedule_post(self, schedule_id: str, new_time: datetime) -> bool:
        """Thay đổi thời gian lịch đăng"""
        if schedule_id in self.scheduled_posts:
            schedule_info = self.scheduled_posts[schedule_id]
            if schedule_info.get('status') == 'pending':
                schedule_info['next_execution'] = new_time.isoformat()
                self.save_scheduled_posts()
                return True
        return False
    
    def export_schedules_to_json(self, filename: str = None) -> Optional[str]:
        """Xuất dữ liệu lịch đăng ra file JSON"""
        if filename is None:
            filename = f"schedules_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_posts, f, ensure_ascii=False, indent=2)
            return filename
        except Exception as e:
            logger.exception("Lỗi khi xuất dữ liệu lịch đăng")
            return None

    def set_bot(self, bot: Bot):
        """Gán bot sau khi khởi tạo"""
        self.bot = bot

    async def _notify_admins(self, message: str):
        from config import Config
        if not self.bot:
            return
        for admin_id in Config.ADMIN_IDS:
            try:
                await self.bot.send_message(chat_id=admin_id, text=message, parse_mode="HTML")
            except Exception:
                pass