#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified bot: kết hợp quản lý nhóm & đăng bài"""

import asyncio
import sys
from telegram import Bot, Update
from telegram.ext import Application
from config import Config
from telegram_bot import TelegramGroupBot
from mass_post_bot import MassPostBot

# Khắc phục event loop cho Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def main():
    token = Config.BOT_TOKEN
    if not token:
        print("❌ Chưa cấu hình BOT_TOKEN trong Config!")
        sys.exit(1)

    # Xoá webhook để bật polling
    try:
        try:
            bot = Bot(token=token)
            # Sử dụng asyncio để chạy hàm bất đồng bộ đúng cách
            asyncio.run(bot.delete_webhook(bot, drop_pending_updates=True))
            # Tạo application dùng chung
    application = Application.builder().token(token).build()

    # Nạp hai module chức năng
    TelegramGroupBot(token, application)
    MassPostBot(token, application)

    print("🤖 Unified bot đang khởi động...")
    print("📱 Nhấn Ctrl+C để dừng bot")

    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("\n🛑 Bot đã dừng!")

if __name__ == "__main__":
    main() 