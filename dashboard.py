#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import asyncio
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session  # type: ignore
from telegram import Bot
from werkzeug.security import check_password_hash, generate_password_hash  # type: ignore
from config import Config
from channel_manager import ChannelManager
from post_manager import PostManager
from scheduler import PostScheduler
from emoji_handler import EmojiHandler
import logging
import concurrent.futures  # Thêm để chạy coroutine trong thread

from telegram import constants as tg_constants

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Thay đổi key này trong production

# Khởi tạo các managers
channel_manager = ChannelManager()
post_manager = PostManager()
scheduler = PostScheduler()
emoji_handler = EmojiHandler()

# Bot Telegram để thao tác quản lý nhóm
telegram_bot = Bot(Config.BOT_TOKEN)
GROUP_ID = Config.MANAGED_GROUP_ID

# Cấu hình dashboard
DASHBOARD_CONFIG = {
    'title': 'Bot Đăng Bài Hàng Loạt - Dashboard',
    'version': '1.0.0',
    'admin_password': '123456',  # Thay đổi password này
}

# === Helper: chạy coroutine an toàn trong dashboard (từ final_dashboard) ===

def run_async_in_thread(coro):
    """Chạy coroutine trong thread riêng để tránh xung đột event loop."""
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(_run)
        return future.result()

# -------------------------------------------------------------------------

@app.route('/')
def index():
    """Trang chủ dashboard"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Lấy thống kê
    stats = get_dashboard_stats()
    
    return render_template('dashboard.html', 
                         title=DASHBOARD_CONFIG['title'],
                         stats=stats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Trang đăng nhập"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == DASHBOARD_CONFIG['admin_password']:
            session['logged_in'] = True
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Mật khẩu không đúng!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Đăng xuất"""
    session.pop('logged_in', None)
    flash('Đã đăng xuất thành công!', 'info')
    return redirect(url_for('login'))

@app.route('/channels')
def channels():
    """Trang quản lý kênh"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    channels_data = list(channel_manager.channels.values())
    return render_template('channels.html', 
                         channels=channels_data,
                         title="Quản lý kênh")

@app.route('/channels/add', methods=['POST'])
def add_channel():
    """Thêm kênh mới"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    data = request.get_json()
    channel_id = data.get('channel_id')
    channel_name = data.get('channel_name')
    
    if not channel_id:
        return jsonify({'error': 'Channel ID là bắt buộc'}), 400
    
    try:
        # Thêm kênh (giả lập - trong thực tế cần check quyền bot)
        # Lưu thông tin kênh vào database
        channel_info = {
            'id': channel_id,
            'name': channel_name or f"Kênh {channel_id}",
            'active': True,
            'added_date': datetime.now().isoformat()
        }
        channel_manager.channels[channel_id] = channel_info
        channel_manager.save_channels()
        return jsonify({'success': True, 'message': 'Đã thêm kênh thành công'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/channels/remove/<channel_id>', methods=['DELETE'])
def remove_channel(channel_id):
    """Xóa kênh"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    try:
        result = channel_manager.remove_channel(channel_id)
        if result:
            return jsonify({'success': True, 'message': 'Đã xóa kênh thành công'})
        else:
            return jsonify({'error': 'Không tìm thấy kênh'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/post')
def post_page():
    """Trang đăng bài"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    channels_data = list(channel_manager.channels.values())
    return render_template('post.html', 
                         channels=channels_data,
                         title="Đăng bài hàng loạt")

@app.route('/posts')
def redirect_post():
    return redirect(url_for('post_page'))

@app.route('/post/send', methods=['POST'])
def send_post():
    """Gửi bài đăng"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    data = request.get_json()
    content = data.get('content')
    selected_channels = data.get('channels', [])
    
    if not content:
        return jsonify({'error': 'Nội dung bài đăng là bắt buộc'}), 400
    
    if not selected_channels:
        return jsonify({'error': 'Vui lòng chọn ít nhất một kênh'}), 400
    
    try:
        # Xử lý emoji
        processed_content = emoji_handler.process_text_with_emoji(content)
        
        results = []
        for channel_id in selected_channels:
            try:
                # Sử dụng helper mới để gửi tin nhắn, kế thừa logic đã test thành công
                run_async_in_thread(
                    telegram_bot.send_message(  # type: ignore
                        chat_id=channel_id,
                        text=processed_content,
                        disable_web_page_preview=True
                    )
                )
                results.append({'channel_id': channel_id, 'status': 'success'})
            except Exception as e:
                results.append({'channel_id': channel_id, 'status': 'error', 'error': str(e)})
        
        return jsonify({
            'success': True,
            'message': f'Đã gửi bài đăng đến {len(selected_channels)} kênh',
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Alias route cho /send để tương thích với mã test cũ
@app.route('/send', methods=['POST'])
def send_post_alias():
    return send_post()

@app.route('/schedule')
def schedule_page():
    """Trang lên lịch"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    channels_data = list(channel_manager.channels.values())
    scheduled_posts = asyncio.run(scheduler.get_scheduled_posts())
    
    return render_template('schedule.html', 
                         channels=channels_data,
                         scheduled_posts=scheduled_posts,
                         title="Lên lịch đăng bài")

@app.route('/schedule/add', methods=['POST'])
def add_schedule():
    """Thêm lịch đăng bài"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    data = request.get_json()
    content = data.get('content')
    channels = data.get('channels', [])
    schedule_time = data.get('schedule_time')
    repeat_type = data.get('repeat_type', 'once')
    
    if not all([content, channels, schedule_time]):
        return jsonify({'error': 'Thiếu thông tin bắt buộc'}), 400
    
    try:
        # Chuyển đổi thời gian
        schedule_datetime = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
        
        # Thêm lịch
        # Chuẩn bị post_data (có thể mở rộng thêm các trường khác nếu cần)
        post_data = {"content": content}
        # Gọi hàm async schedule_post
        schedule_id = asyncio.run(scheduler.schedule_post(
            post_data=post_data,
            channels=channels,
            scheduled_time=schedule_datetime,
            repeat_type=repeat_type
        ))
        
        return jsonify({
            'success': True,
            'message': 'Đã thêm lịch đăng bài thành công',
            'schedule_id': schedule_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/schedule/cancel/<schedule_id>', methods=['DELETE'])
def cancel_schedule(schedule_id):
    """Hủy lịch đăng bài"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    try:
        result = asyncio.run(scheduler.cancel_schedule(schedule_id))
        if result:
            return jsonify({'success': True, 'message': 'Đã hủy lịch đăng bài'})
        else:
            return jsonify({'error': 'Không tìm thấy lịch đăng bài'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/emoji')
def emoji_page():
    """Trang công cụ emoji"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    return render_template('emoji.html', title="Công cụ Emoji")

@app.route('/emoji/process', methods=['POST'])
def process_emoji():
    """Xử lý emoji"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    data = request.get_json()
    text = data.get('text', '')
    
    try:
        processed_text = emoji_handler.process_text_with_emoji(text)
        suggestions = emoji_handler.suggest_emoji_for_text(text)
        
        return jsonify({
            'success': True,
            'original_text': text,
            'processed_text': processed_text,
            'suggestions': suggestions
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/group')
def group_page():
    """Trang quản lý nhóm"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if GROUP_ID == 0:
        flash('Chưa cấu hình MANAGED_GROUP_ID trong .env hoặc Config.py', 'error')
        return redirect(url_for('index'))

    # Lấy danh sách admins và số thành viên
    try:
        admins = asyncio.run(telegram_bot.get_chat_administrators(GROUP_ID))  # type: ignore
        member_count = asyncio.run(telegram_bot.get_chat_member_count(GROUP_ID))  # type: ignore
    except Exception as e:
        admins = []
        member_count = 'N/A'
        flash(f'Lỗi khi lấy thông tin nhóm: {e}', 'error')

    return render_template('group.html', admins=admins, member_count=member_count, title='Quản lý nhóm')

@app.route('/api/group/kick', methods=['POST'])
def api_kick_member():
    if not session.get('logged_in'):
        return jsonify({'error': 'Chưa đăng nhập'}), 401

    if GROUP_ID == 0:
        return jsonify({'error': 'Chưa cấu hình MANAGED_GROUP_ID'}), 400

    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'Thiếu user_id'}), 400

    try:
        asyncio.run(telegram_bot.ban_chat_member(GROUP_ID, int(user_id)))  # type: ignore
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/group/unban', methods=['POST'])
def api_unban_member():
    if not session.get('logged_in'):
        return jsonify({'error': 'Chưa đăng nhập'}), 401

    if GROUP_ID == 0:
        return jsonify({'error': 'Chưa cấu hình MANAGED_GROUP_ID'}), 400

    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'Thiếu user_id'}), 400

    try:
        asyncio.run(telegram_bot.unban_chat_member(GROUP_ID, int(user_id)))  # type: ignore
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """API lấy thống kê"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    stats = get_dashboard_stats()
    return jsonify(stats)

def get_dashboard_stats():
    """Lấy thống kê dashboard"""
    try:
        channels_data = list(channel_manager.channels.values())
        scheduled_posts = asyncio.run(scheduler.get_scheduled_posts())
        
        stats = {
            'total_channels': len(channels_data),
            'active_channels': len([c for c in channels_data if c.get('active', True)]),
            'scheduled_posts': len(scheduled_posts),
            'posts_today': 0,  # Tính toán từ database
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            'total_channels': 0,
            'active_channels': 0,
            'scheduled_posts': 0,
            'posts_today': 0,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

if __name__ == '__main__':
    print("🌐 Bảng điều khiển web đang khởi động...")
    print("📊 Dashboard URL: http://localhost:5000")
    print("🔑 Mật khẩu mặc định: 123456")
    print("💡 Nhấn Ctrl+C để dừng dashboard")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 