#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import threading
from flask import Flask, render_template_string, request, jsonify
from telegram import Bot
from config import Config

app = Flask(__name__)
bot = Bot(Config.BOT_TOKEN)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Đăng bài Telegram</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial; margin: 50px; }
        .container { max-width: 600px; }
        textarea { width: 100%; height: 200px; margin: 10px 0; }
        select { width: 100%; height: 150px; margin: 10px 0; }
        button { padding: 15px 30px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        .result { margin-top: 20px; padding: 10px; background: #f0f0f0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Đăng bài lên Telegram</h1>
        
        <label>Nội dung bài đăng:</label>
        <textarea id="content" placeholder="Nhập nội dung bài đăng..."></textarea>
        
        <label>Chọn kênh:</label>
        <select id="channels" multiple>
            <option value="-1002376181681">🇧🇷 ABCDBET | Canal oficial🍀</option>
            <option value="@testchannel">Test Channel</option>
        </select>
        
        <br><br>
        <button onclick="postMessage()">📢 ĐĂNG BÀI NGAY</button>
        
        <div id="result" class="result" style="display:none;"></div>
    </div>

    <script>
        async function postMessage() {
            const content = document.getElementById('content').value;
            const channelSelect = document.getElementById('channels');
            const channels = Array.from(channelSelect.selectedOptions).map(option => option.value);
            
            if (!content.trim()) {
                alert('Vui lòng nhập nội dung!');
                return;
            }
            
            if (channels.length === 0) {
                alert('Vui lòng chọn ít nhất một kênh!');
                return;
            }
            
            try {
                const response = await fetch('/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({content, channels})
                });
                
                const result = await response.json();
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                
                if (result.success) {
                    resultDiv.innerHTML = `<h3>✅ THÀNH CÔNG!</h3><p>Đã đăng bài lên ${result.sent_count} kênh</p>`;
                    resultDiv.style.background = '#d4edda';
                } else {
                    resultDiv.innerHTML = `<h3>❌ LỖI!</h3><p>${result.error}</p>`;
                    resultDiv.style.background = '#f8d7da';
                }
            } catch (error) {
                document.getElementById('result').innerHTML = `<h3>❌ LỖI MẠNG!</h3><p>${error}</p>`;
            }
        }
    </script>
</body>
</html>
"""

def run_async_in_thread(coro):
    """Chạy coroutine trong thread riêng để tránh lỗi event loop"""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        return future.result()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    content = data.get('content', '').strip()
    channels = data.get('channels', [])
    
    if not content:
        return jsonify({'success': False, 'error': 'Nội dung trống!'})
    
    if not channels:
        return jsonify({'success': False, 'error': 'Chưa chọn kênh!'})
    
    sent_count = 0
    errors = []
    
    for channel in channels:
        try:
            run_async_in_thread(bot.send_message(chat_id=channel, text=content))
            sent_count += 1
        except Exception as e:
            errors.append(f"Kênh {channel}: {str(e)}")
    
    if sent_count > 0:
        return jsonify({
            'success': True, 
            'sent_count': sent_count,
            'errors': errors if errors else None
        })
    else:
        return jsonify({
            'success': False, 
            'error': f"Không gửi được kênh nào: {'; '.join(errors)}"
        })

if __name__ == '__main__':
    print("🚀 Dashboard mới đang khởi động...")
    print("📱 Mở: http://localhost:9000")
    app.run(host='0.0.0.0', port=9000, debug=True) 