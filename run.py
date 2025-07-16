
import sys
import os
import logging
from config import Config
from mass_post_bot import MassPostBot

logging.basicConfig(level=logging.INFO)

def main():
    """Chạy bot đăng bài hàng loạt với cấu hình từ config.py"""
    # Kiểm tra token
    if not hasattr(Config, 'BOT_TOKEN') or not Config.BOT_TOKEN:
        print("❌ Lỗi: Không tìm thấy BOT_TOKEN!")
        print("🔧 Vui lòng:")
        print("   1. Tạo file .env trong thư mục gốc")
        print("   2. Thêm dòng: BOT_TOKEN=your_bot_token_here")
        print("   3. Thay thế your_bot_token_here bằng token từ @BotFather")
        sys.exit(1)

    # Kiểm tra admin IDs
    if not hasattr(Config, 'ADMIN_IDS') or not Config.ADMIN_IDS:
        print("⚠️ Cảnh báo: Không có admin nào được cấu hình!")
        print("💡 Thêm ADMIN_IDS vào file .env để sử dụng đầy đủ chức năng")
        print("   Ví dụ: ADMIN_IDS=123456789,987654321")

    # Hiển thị thông tin cấu hình
    print("🚀 Bot Đăng Bài Hàng Loạt Telegram")
    print("=" * 50)
    print(f"📋 Token: {getattr(Config, 'BOT_TOKEN', '')[:10]}...")
    print(f"👥 Admin IDs: {getattr(Config, 'ADMIN_IDS', [])}")
    print(f"📢 Delay giữa các lần đăng: {getattr(Config, 'DEFAULT_DELAY_BETWEEN_POSTS', 5)} giây")
    print(f"📊 Số kênh tối đa mỗi lần: {getattr(Config, 'MAX_CHANNELS_PER_POST', 50)}")
    print(f"⏰ Interval check scheduler: {getattr(Config, 'SCHEDULER_CHECK_INTERVAL', 30)} giây")
    print(f"🗂️ File database kênh: {getattr(Config, 'CHANNELS_DB_FILE', 'channels.json')}")
    print(f"📝 File database bài đăng: {getattr(Config, 'POSTS_DB_FILE', 'posts.json')}")
    print(f"🔄 Auto backup: {'Bật' if getattr(Config, 'ENABLE_AUTO_BACKUP', False) else 'Tắt'}")
    print("=" * 50)

    # Khởi tạo và chạy bot
    try:
        bot = MassPostBot(Config.BOT_TOKEN)
        print("✅ Bot đã khởi tạo thành công!")
        print("🚀 Đang kết nối với Telegram...")
        print("📱 Gõ /start để bắt đầu sử dụng")
        bot.run()
    except Exception as e:
        print(f"❌ Lỗi khi khởi tạo/chạy bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()