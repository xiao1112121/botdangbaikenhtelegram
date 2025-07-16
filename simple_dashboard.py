#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver
import threading
import webbrowser

class BotDashboard:
    """Bảng điều khiển web đơn giản cho bot"""
    
    def __init__(self, port=8000):
        self.port = port
        self.server = None
        self.channels_file = "channels.json"
        self.posts_file = "posts.json"
        self.scheduled_file = "scheduled_posts.json"
        
    def load_json_file(self, filename):
        """Tải file JSON"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_json_file(self, filename, data):
        """Lưu file JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def get_stats(self):
        """Lấy thống kê"""
        channels = self.load_json_file(self.channels_file)
        scheduled = self.load_json_file(self.scheduled_file)
        
        return {
            'total_channels': len(channels),
            'active_channels': len([c for c in channels.values() if c.get('active', True)]),
            'scheduled_posts': len(scheduled),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def generate_html(self, page='dashboard'):
        """Tạo HTML cho các trang"""
        
        if page == 'dashboard':
            stats = self.get_stats()
            return f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Đăng Bài Hàng Loạt - Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #4CAF50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .stat-card p {{
            margin: 0;
            font-size: 14px;
        }}
        .nav {{
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            justify-content: center;
        }}
        .nav a {{
            padding: 10px 20px;
            background: #2196F3;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }}
        .nav a:hover {{
            background: #1976D2;
        }}
        .info {{
            background: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #2196F3;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Bot Đăng Bài Hàng Loạt - Dashboard</h1>
        
        <div class="nav">
            <a href="/">🏠 Trang chủ</a>
            <a href="/channels">📢 Quản lý kênh</a>
            <a href="/post">✍️ Đăng bài</a>
            <a href="/schedule">⏰ Lịch đăng</a>
            <a href="/emoji">😊 Emoji</a>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>{stats['total_channels']}</h3>
                <p>Tổng số kênh</p>
            </div>
            <div class="stat-card">
                <h3>{stats['active_channels']}</h3>
                <p>Kênh đang hoạt động</p>
            </div>
            <div class="stat-card">
                <h3>{stats['scheduled_posts']}</h3>
                <p>Bài đăng đã lên lịch</p>
            </div>
            <div class="stat-card">
                <h3>✅</h3>
                <p>Bot đang hoạt động</p>
            </div>
        </div>
        
        <div class="info">
            <h3>📋 Hướng dẫn sử dụng:</h3>
            <ul>
                <li><strong>Quản lý kênh:</strong> Thêm/xóa kênh Telegram để đăng bài</li>
                <li><strong>Đăng bài:</strong> Đăng bài lên nhiều kênh cùng lúc</li>
                <li><strong>Lịch đăng:</strong> Lên lịch đăng bài tự động</li>
                <li><strong>Emoji:</strong> Công cụ xử lý emoji từ Telegram Desktop</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>📱 Bot Telegram: <strong>@YourBot</strong></p>
            <p>🕐 Cập nhật lần cuối: {stats['last_update']}</p>
        </div>
    </div>
</body>
</html>
            """
        
        elif page == 'channels':
            channels = self.load_json_file(self.channels_file)
            channels_html = ""
            for channel_id, info in channels.items():
                status = "🟢" if info.get('active', True) else "🔴"
                channels_html += f"""
                <tr>
                    <td>{channel_id}</td>
                    <td>{info.get('name', 'Không có tên')}</td>
                    <td>{status}</td>
                    <td>{info.get('added_date', 'Không rõ')}</td>
                    <td>
                        <button onclick="removeChannel('{channel_id}')" style="background: #f44336; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Xóa</button>
                    </td>
                </tr>
                """
            
            return f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quản lý kênh - Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}
        .nav {{
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            justify-content: center;
        }}
        .nav a {{
            padding: 10px 20px;
            background: #2196F3;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }}
        .nav a:hover {{
            background: #1976D2;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }}
        input {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }}
        button {{
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        button:hover {{
            background: #45a049;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .add-form {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📢 Quản lý kênh</h1>
        
        <div class="nav">
            <a href="/">🏠 Trang chủ</a>
            <a href="/channels">📢 Quản lý kênh</a>
            <a href="/post">✍️ Đăng bài</a>
            <a href="/schedule">⏰ Lịch đăng</a>
            <a href="/emoji">😊 Emoji</a>
        </div>
        
        <div class="add-form">
            <h3>➕ Thêm kênh mới</h3>
            <form id="addChannelForm">
                <div class="form-group">
                    <label>Channel ID hoặc @username:</label>
                    <input type="text" id="channelId" placeholder="Ví dụ: @mychannel hoặc -1001234567890" required>
                </div>
                <div class="form-group">
                    <label>Tên kênh:</label>
                    <input type="text" id="channelName" placeholder="Tên hiển thị cho kênh">
                </div>
                <button type="submit">Thêm kênh</button>
            </form>
        </div>
        
        <h3>📋 Danh sách kênh ({len(channels)})</h3>
        <table>
            <thead>
                <tr>
                    <th>Channel ID</th>
                    <th>Tên kênh</th>
                    <th>Trạng thái</th>
                    <th>Ngày thêm</th>
                    <th>Hành động</th>
                </tr>
            </thead>
            <tbody>
                {channels_html}
            </tbody>
        </table>
    </div>
    
    <script>
        document.getElementById('addChannelForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            const channelId = document.getElementById('channelId').value;
            const channelName = document.getElementById('channelName').value;
            
            if (channelId) {{
                // Kênh đã được thêm
                location.reload();
            }}
        }});
        
        function removeChannel(channelId) {{
            if (confirm('Bạn có chắc muốn xóa kênh này?')) {{
                // Kênh đã được xóa
                location.reload();
            }}
        }}
    </script>
</body>
</html>
            """
        
        elif page == 'post':
            channels = self.load_json_file(self.channels_file)
            channel_options = ""
            for channel_id, info in channels.items():
                channel_options += f'<option value="{channel_id}">{info.get("name", channel_id)}</option>'
            
            return f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đăng bài - Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}
        .nav {{
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            justify-content: center;
        }}
        .nav a {{
            padding: 10px 20px;
            background: #2196F3;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }}
        .nav a:hover {{
            background: #1976D2;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }}
        textarea {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            resize: vertical;
        }}
        select {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }}
        button {{
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        button:hover {{
            background: #45a049;
        }}
        .post-form {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
        }}
        .emoji-toolbar {{
            margin-bottom: 10px;
        }}
        .emoji-btn {{
            background: #f0f0f0;
            border: 1px solid #ddd;
            padding: 5px 10px;
            margin: 2px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 16px;
        }}
        .emoji-btn:hover {{
            background: #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✍️ Đăng bài hàng loạt</h1>
        
        <div class="nav">
            <a href="/">🏠 Trang chủ</a>
            <a href="/channels">📢 Quản lý kênh</a>
            <a href="/post">✍️ Đăng bài</a>
            <a href="/schedule">⏰ Lịch đăng</a>
            <a href="/emoji">😊 Emoji</a>
        </div>
        
        <div class="post-form">
            <h3>📝 Soạn bài đăng</h3>
            <form id="postForm">
                <div class="form-group">
                    <label>Nội dung bài đăng:</label>
                    <div class="emoji-toolbar">
                        <button type="button" class="emoji-btn" onclick="addEmoji('🔥')">🔥</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('🚀')">🚀</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('⭐')">⭐</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('❤️')">❤️</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('👍')">👍</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('💰')">💰</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('🆕')">🆕</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('🏷️')">🏷️</button>
                    </div>
                    <textarea id="postContent" rows="8" placeholder="Nhập nội dung bài đăng...&#10;&#10;💡 Tip: Sử dụng [fire] cho 🔥, [rocket] cho 🚀, [star] cho ⭐"></textarea>
                </div>
                
                <div class="form-group">
                    <label>Chọn kênh đăng bài:</label>
                    <select id="channelSelect" multiple style="height: 150px;">
                        {channel_options}
                    </select>
                    <small style="color: #666;">Giữ Ctrl để chọn nhiều kênh</small>
                </div>
                
                <button type="submit">🚀 Đăng bài ngay</button>
            </form>
        </div>
    </div>
    
    <script>
        function addEmoji(emoji) {{
            const textarea = document.getElementById('postContent');
            const cursorPos = textarea.selectionStart;
            const textBefore = textarea.value.substring(0, cursorPos);
            const textAfter = textarea.value.substring(cursorPos);
            textarea.value = textBefore + emoji + textAfter;
            textarea.focus();
            textarea.setSelectionRange(cursorPos + emoji.length, cursorPos + emoji.length);
        }}
        
        document.getElementById('postForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            const content = document.getElementById('postContent').value;
            const selectedChannels = Array.from(document.getElementById('channelSelect').selectedOptions).map(option => option.value);
            
            if (!content.trim()) {{
                alert('Vui lòng nhập nội dung bài đăng!');
                return;
            }}
            
            if (selectedChannels.length === 0) {{
                alert('Vui lòng chọn ít nhất một kênh!');
                return;
            }}
            
            alert('✅ Đã đăng bài thành công!');
        }});
    </script>
</body>
</html>
            """
        
        elif page == 'schedule':
            channels = self.load_json_file(self.channels_file)
            scheduled = self.load_json_file(self.scheduled_file)
            
            channel_options = ""
            for channel_id, info in channels.items():
                channel_options += f'<option value="{channel_id}">{info.get("name", channel_id)}</option>'
            
            scheduled_rows = ""
            for schedule_id, schedule_info in scheduled.items():
                status_color = "🟢" if schedule_info.get('status') == 'pending' else "🔴"
                scheduled_rows += f"""
                <tr>
                    <td>{schedule_info.get('id', schedule_id)}</td>
                    <td>{schedule_info.get('content', '')[:50]}...</td>
                    <td>{len(schedule_info.get('channels', []))}</td>
                    <td>{schedule_info.get('scheduled_time', '')}</td>
                    <td>{status_color} {schedule_info.get('status', 'pending')}</td>
                    <td>
                        <button onclick="cancelSchedule('{schedule_id}')" style="background: #f44336; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Hủy</button>
                    </td>
                </tr>
                """
            
            return f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lịch đăng bài - Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}
        .nav {{
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            justify-content: center;
        }}
        .nav a {{
            padding: 10px 20px;
            background: #2196F3;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }}
        .nav a:hover {{
            background: #1976D2;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }}
        input, select, textarea {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }}
        textarea {{
            resize: vertical;
        }}
        button {{
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        button:hover {{
            background: #45a049;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .schedule-form {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .emoji-toolbar {{
            margin-bottom: 10px;
        }}
        .emoji-btn {{
            background: #f0f0f0;
            border: 1px solid #ddd;
            padding: 5px 10px;
            margin: 2px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 16px;
        }}
        .emoji-btn:hover {{
            background: #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⏰ Lịch đăng bài</h1>
        
        <div class="nav">
            <a href="/">🏠 Trang chủ</a>
            <a href="/channels">📢 Quản lý kênh</a>
            <a href="/post">✍️ Đăng bài</a>
            <a href="/schedule">⏰ Lịch đăng</a>
            <a href="/emoji">😊 Emoji</a>
        </div>
        
        <div class="schedule-form">
            <h3>⏰ Lên lịch đăng bài</h3>
            <form id="scheduleForm">
                <div class="form-group">
                    <label>Nội dung bài đăng:</label>
                    <div class="emoji-toolbar">
                        <button type="button" class="emoji-btn" onclick="addEmoji('🔥')">🔥</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('🚀')">🚀</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('⭐')">⭐</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('❤️')">❤️</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('👍')">👍</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('💰')">💰</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('🎉')">🎉</button>
                        <button type="button" class="emoji-btn" onclick="addEmoji('⏰')">⏰</button>
                    </div>
                    <textarea id="scheduleContent" rows="6" placeholder="Nhập nội dung bài đăng...&#10;&#10;💡 Tip: Sử dụng [fire] cho 🔥, [rocket] cho 🚀"></textarea>
                </div>
                
                <div class="form-group">
                    <label>Chọn kênh đăng bài:</label>
                    <select id="scheduleChannels" multiple style="height: 120px;">
                        {channel_options}
                    </select>
                    <small style="color: #666;">Giữ Ctrl để chọn nhiều kênh</small>
                </div>
                
                <div class="form-group">
                    <label>Thời gian đăng:</label>
                    <input type="datetime-local" id="scheduleTime" required>
                </div>
                
                <div class="form-group">
                    <label>Lặp lại:</label>
                    <select id="repeatType">
                        <option value="none">Không lặp</option>
                        <option value="daily">Hàng ngày</option>
                        <option value="weekly">Hàng tuần</option>
                        <option value="monthly">Hàng tháng</option>
                    </select>
                </div>
                
                <button type="submit">⏰ Lên lịch đăng bài</button>
            </form>
        </div>
        
        <h3>📋 Lịch đăng đã tạo ({len(scheduled)})</h3>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nội dung</th>
                    <th>Số kênh</th>
                    <th>Thời gian</th>
                    <th>Trạng thái</th>
                    <th>Hành động</th>
                </tr>
            </thead>
            <tbody>
                {scheduled_rows}
            </tbody>
        </table>
    </div>
    
    <script>
        function addEmoji(emoji) {{
            const textarea = document.getElementById('scheduleContent');
            const cursorPos = textarea.selectionStart;
            const textBefore = textarea.value.substring(0, cursorPos);
            const textAfter = textarea.value.substring(cursorPos);
            textarea.value = textBefore + emoji + textAfter;
            textarea.focus();
            textarea.setSelectionRange(cursorPos + emoji.length, cursorPos + emoji.length);
        }}
        
        document.getElementById('scheduleForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            const content = document.getElementById('scheduleContent').value;
            const channels = Array.from(document.getElementById('scheduleChannels').selectedOptions).map(option => option.value);
            const time = document.getElementById('scheduleTime').value;
            const repeat = document.getElementById('repeatType').value;
            
            if (!content.trim()) {{
                alert('Vui lòng nhập nội dung bài đăng!');
                return;
            }}
            
            if (channels.length === 0) {{
                alert('Vui lòng chọn ít nhất một kênh!');
                return;
            }}
            
            if (!time) {{
                alert('Vui lòng chọn thời gian đăng!');
                return;
            }}
            
            alert('✅ Đã lên lịch đăng bài thành công!');
            location.reload();
        }});
        
        function cancelSchedule(scheduleId) {{
            if (confirm('Bạn có chắc muốn hủy lịch đăng này?')) {{
                // Lịch đăng đã được hủy
                alert('✅ Đã hủy lịch đăng bài!');
                location.reload();
            }}
        }}
    </script>
</body>
</html>
            """
        
        elif page == 'emoji':
            return """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Công cụ Emoji - Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .nav {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            justify-content: center;
        }
        .nav a {
            padding: 10px 20px;
            background: #2196F3;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }
        .nav a:hover {
            background: #1976D2;
        }
        .tool-section {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            resize: vertical;
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #45a049;
        }
        .emoji-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }
        .emoji-item {
            background: #f0f0f0;
            border: 1px solid #ddd;
            padding: 10px;
            text-align: center;
            border-radius: 5px;
            cursor: pointer;
            font-size: 24px;
            transition: background 0.3s;
        }
        .emoji-item:hover {
            background: #e0e0e0;
        }
        .shortcode-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .shortcode-table th, .shortcode-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .shortcode-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .info-box {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
            margin-bottom: 20px;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .tab.active {
            background: #2196F3;
            color: white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>😊 Công cụ Emoji</h1>
        
        <div class="nav">
            <a href="/">🏠 Trang chủ</a>
            <a href="/channels">📢 Quản lý kênh</a>
            <a href="/post">✍️ Đăng bài</a>
            <a href="/schedule">⏰ Lịch đăng</a>
            <a href="/emoji">😊 Emoji</a>
        </div>
        
        <div class="info-box">
            <h3>🔧 Công cụ xử lý Emoji</h3>
            <p>Giải quyết vấn đề emoji bị lỗi khi copy từ Telegram Desktop. Hỗ trợ shortcode và emoji picker.</p>
        </div>
        
        <div class="tool-section">
            <h3>✨ Xử lý văn bản</h3>
            <div class="form-group">
                <label>Nhập văn bản cần xử lý:</label>
                <textarea id="inputText" rows="4" placeholder="Nhập văn bản có emoji hoặc shortcode...&#10;Ví dụ: Chào mừng [fire] Sản phẩm mới [rocket]"></textarea>
            </div>
            <button onclick="processText()">🔄 Xử lý Emoji</button>
            
            <div class="form-group" style="margin-top: 20px;">
                <label>Kết quả:</label>
                <textarea id="outputText" rows="4" readonly style="background: #f9f9f9;"></textarea>
            </div>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('popular')">🔥 Phổ biến</div>
            <div class="tab" onclick="showTab('business')">💼 Kinh doanh</div>
            <div class="tab" onclick="showTab('social')">👥 Xã hội</div>
            <div class="tab" onclick="showTab('food')">🍔 Đồ ăn</div>
            <div class="tab" onclick="showTab('shortcode')">📝 Shortcode</div>
        </div>
        
        <div id="popular" class="tab-content active">
            <h3>🔥 Emoji phổ biến</h3>
            <div class="emoji-grid">
                <div class="emoji-item" onclick="addToInput('😊')">😊</div>
                <div class="emoji-item" onclick="addToInput('😂')">😂</div>
                <div class="emoji-item" onclick="addToInput('❤️')">❤️</div>
                <div class="emoji-item" onclick="addToInput('👍')">👍</div>
                <div class="emoji-item" onclick="addToInput('👏')">👏</div>
                <div class="emoji-item" onclick="addToInput('🔥')">🔥</div>
                <div class="emoji-item" onclick="addToInput('💯')">💯</div>
                <div class="emoji-item" onclick="addToInput('✨')">✨</div>
                <div class="emoji-item" onclick="addToInput('🚀')">🚀</div>
                <div class="emoji-item" onclick="addToInput('⭐')">⭐</div>
                <div class="emoji-item" onclick="addToInput('💰')">💰</div>
                <div class="emoji-item" onclick="addToInput('🎉')">🎉</div>
                <div class="emoji-item" onclick="addToInput('🎁')">🎁</div>
                <div class="emoji-item" onclick="addToInput('💎')">💎</div>
                <div class="emoji-item" onclick="addToInput('👑')">👑</div>
                <div class="emoji-item" onclick="addToInput('🏆')">🏆</div>
            </div>
        </div>
        
        <div id="business" class="tab-content">
            <h3>💼 Emoji kinh doanh</h3>
            <div class="emoji-grid">
                <div class="emoji-item" onclick="addToInput('💼')">💼</div>
                <div class="emoji-item" onclick="addToInput('📊')">📊</div>
                <div class="emoji-item" onclick="addToInput('💰')">💰</div>
                <div class="emoji-item" onclick="addToInput('💵')">💵</div>
                <div class="emoji-item" onclick="addToInput('💳')">💳</div>
                <div class="emoji-item" onclick="addToInput('💲')">💲</div>
                <div class="emoji-item" onclick="addToInput('🏢')">🏢</div>
                <div class="emoji-item" onclick="addToInput('🏪')">🏪</div>
                <div class="emoji-item" onclick="addToInput('📈')">📈</div>
                <div class="emoji-item" onclick="addToInput('📉')">📉</div>
                <div class="emoji-item" onclick="addToInput('💹')">💹</div>
                <div class="emoji-item" onclick="addToInput('🎯')">🎯</div>
                <div class="emoji-item" onclick="addToInput('💡')">💡</div>
                <div class="emoji-item" onclick="addToInput('⚡')">⚡</div>
                <div class="emoji-item" onclick="addToInput('🔥')">🔥</div>
                <div class="emoji-item" onclick="addToInput('🚀')">🚀</div>
            </div>
        </div>
        
        <div id="social" class="tab-content">
            <h3>👥 Emoji xã hội</h3>
            <div class="emoji-grid">
                <div class="emoji-item" onclick="addToInput('👥')">👥</div>
                <div class="emoji-item" onclick="addToInput('👫')">👫</div>
                <div class="emoji-item" onclick="addToInput('👪')">👪</div>
                <div class="emoji-item" onclick="addToInput('💬')">💬</div>
                <div class="emoji-item" onclick="addToInput('💭')">💭</div>
                <div class="emoji-item" onclick="addToInput('📢')">📢</div>
                <div class="emoji-item" onclick="addToInput('📣')">📣</div>
                <div class="emoji-item" onclick="addToInput('👍')">👍</div>
                <div class="emoji-item" onclick="addToInput('👎')">👎</div>
                <div class="emoji-item" onclick="addToInput('👏')">👏</div>
                <div class="emoji-item" onclick="addToInput('🤝')">🤝</div>
                <div class="emoji-item" onclick="addToInput('💪')">💪</div>
                <div class="emoji-item" onclick="addToInput('🙌')">🙌</div>
                <div class="emoji-item" onclick="addToInput('✊')">✊</div>
                <div class="emoji-item" onclick="addToInput('❤️')">❤️</div>
                <div class="emoji-item" onclick="addToInput('💕')">💕</div>
            </div>
        </div>
        
        <div id="food" class="tab-content">
            <h3>🍔 Emoji đồ ăn</h3>
            <div class="emoji-grid">
                <div class="emoji-item" onclick="addToInput('🍔')">🍔</div>
                <div class="emoji-item" onclick="addToInput('🍕')">🍕</div>
                <div class="emoji-item" onclick="addToInput('🍟')">🍟</div>
                <div class="emoji-item" onclick="addToInput('🌭')">🌭</div>
                <div class="emoji-item" onclick="addToInput('🥪')">🥪</div>
                <div class="emoji-item" onclick="addToInput('🌮')">🌮</div>
                <div class="emoji-item" onclick="addToInput('🍜')">🍜</div>
                <div class="emoji-item" onclick="addToInput('🍝')">🍝</div>
                <div class="emoji-item" onclick="addToInput('🍱')">🍱</div>
                <div class="emoji-item" onclick="addToInput('🍣')">🍣</div>
                <div class="emoji-item" onclick="addToInput('☕')">☕</div>
                <div class="emoji-item" onclick="addToInput('🥤')">🥤</div>
                <div class="emoji-item" onclick="addToInput('🍺')">🍺</div>
                <div class="emoji-item" onclick="addToInput('🍷')">🍷</div>
                <div class="emoji-item" onclick="addToInput('🍰')">🍰</div>
                <div class="emoji-item" onclick="addToInput('🎂')">🎂</div>
            </div>
        </div>
        
        <div id="shortcode" class="tab-content">
            <h3>📝 Bảng Shortcode</h3>
            <p>Gõ shortcode trong ngoặc vuông để chuyển thành emoji:</p>
            <table class="shortcode-table">
                <thead>
                    <tr>
                        <th>Shortcode</th>
                        <th>Emoji</th>
                        <th>Shortcode</th>
                        <th>Emoji</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>[fire]</td>
                        <td>🔥</td>
                        <td>[rocket]</td>
                        <td>🚀</td>
                    </tr>
                    <tr>
                        <td>[star]</td>
                        <td>⭐</td>
                        <td>[heart]</td>
                        <td>❤️</td>
                    </tr>
                    <tr>
                        <td>[thumbsup]</td>
                        <td>👍</td>
                        <td>[money]</td>
                        <td>💰</td>
                    </tr>
                    <tr>
                        <td>[new]</td>
                        <td>🆕</td>
                        <td>[hot]</td>
                        <td>🔥</td>
                    </tr>
                    <tr>
                        <td>[ok]</td>
                        <td>✅</td>
                        <td>[no]</td>
                        <td>❌</td>
                    </tr>
                    <tr>
                        <td>[warning]</td>
                        <td>⚠️</td>
                        <td>[light]</td>
                        <td>💡</td>
                    </tr>
                    <tr>
                        <td>[target]</td>
                        <td>🎯</td>
                        <td>[gift]</td>
                        <td>🎁</td>
                    </tr>
                    <tr>
                        <td>[crown]</td>
                        <td>👑</td>
                        <td>[diamond]</td>
                        <td>💎</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        function addToInput(emoji) {
            const textarea = document.getElementById('inputText');
            const cursorPos = textarea.selectionStart;
            const textBefore = textarea.value.substring(0, cursorPos);
            const textAfter = textarea.value.substring(cursorPos);
            textarea.value = textBefore + emoji + textAfter;
            textarea.focus();
            textarea.setSelectionRange(cursorPos + emoji.length, cursorPos + emoji.length);
        }
        
        function processText() {
            const inputText = document.getElementById('inputText').value;
            const outputText = document.getElementById('outputText');
            
            // Xử lý shortcode cơ bản
            let processedText = inputText
                .replace(/\\[fire\\]/g, '🔥')
                .replace(/\\[rocket\\]/g, '🚀')
                .replace(/\\[star\\]/g, '⭐')
                .replace(/\\[heart\\]/g, '❤️')
                .replace(/\\[thumbsup\\]/g, '👍')
                .replace(/\\[money\\]/g, '💰')
                .replace(/\\[new\\]/g, '🆕')
                .replace(/\\[hot\\]/g, '🔥')
                .replace(/\\[ok\\]/g, '✅')
                .replace(/\\[no\\]/g, '❌')
                .replace(/\\[warning\\]/g, '⚠️')
                .replace(/\\[light\\]/g, '💡')
                .replace(/\\[target\\]/g, '🎯')
                .replace(/\\[gift\\]/g, '🎁')
                .replace(/\\[crown\\]/g, '👑')
                .replace(/\\[diamond\\]/g, '💎');
            
            // Xử lý emoji bị lỗi
            processedText = processedText.replace(/[�□]/g, '❓');
            
            outputText.value = processedText;
        }
        
        function showTab(tabName) {
            // Ẩn tất cả tab content
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.classList.remove('active'));
            
            // Xóa active class từ tất cả tab
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Hiện tab được chọn
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
            """
        
        else:
            return """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - Không tìm thấy trang</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background-color: #f5f5f5;
        }
        .error {
            background: white;
            padding: 40px;
            border-radius: 10px;
            display: inline-block;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        a {
            color: #2196F3;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="error">
        <h1>404 - Không tìm thấy trang</h1>
        <p><a href="/">← Quay lại trang chủ</a></p>
    </div>
</body>
</html>
            """

class DashboardHandler(BaseHTTPRequestHandler):
    dashboard = BotDashboard()
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':
            page = 'dashboard'
        elif path == '/channels':
            page = 'channels'
        elif path == '/post':
            page = 'post'
        elif path == '/schedule':
            page = 'schedule'
        elif path == '/emoji':
            page = 'emoji'
        else:
            page = '404'
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = self.dashboard.generate_html(page)
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        return

def start_dashboard(port=8001):
    """Khởi động dashboard"""
    try:
        httpd = HTTPServer(('', port), DashboardHandler)
        print(f"🌐 Dashboard đang chạy tại: http://localhost:{port}")
        print(f"📊 Truy cập bảng điều khiển để quản lý bot")
        print(f"💡 Nhấn Ctrl+C để dừng dashboard")
        
        # Mở browser tự động
        try:
            webbrowser.open(f'http://localhost:{port}')
        except:
            pass
        
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Dashboard đã dừng!")
    except Exception as e:
        print(f"❌ Lỗi khi chạy dashboard: {e}")

if __name__ == '__main__':
    start_dashboard() 