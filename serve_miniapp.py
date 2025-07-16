#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import http.server
import socketserver
import os
from pathlib import Path

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent / "telegram-mini-app"), **kwargs)
    
    def end_headers(self):
        # Thêm CORS headers cho Telegram WebApp
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    PORT = 8080
    
    # Kiểm tra thư mục tồn tại
    mini_app_dir = Path(__file__).parent / "telegram-mini-app"
    if not mini_app_dir.exists():
        print(f"❌ Thư mục {mini_app_dir} không tồn tại!")
        exit(1)
    
    # Kiểm tra file index.html
    index_file = mini_app_dir / "index.html"
    if not index_file.exists():
        print(f"❌ File {index_file} không tồn tại!")
        exit(1)
    
    print(f"🌐 Serving mini-app từ: {mini_app_dir}")
    print(f"🔗 Local URL: http://localhost:{PORT}")
    print(f"📱 Để sử dụng với Telegram, cần expose qua ngrok:")
    print(f"   ngrok http {PORT}")
    print("\n🛑 Nhấn Ctrl+C để dừng server")
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server đã dừng!") 