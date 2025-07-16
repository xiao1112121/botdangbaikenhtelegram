import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Bot Token từ BotFather
    BOT_TOKEN = "7517631725:AAG3kpgUfWWJMQ32YF-LNTU294bdZzEpaaY"
    
    # Cấu hình Admin - Thêm user ID Telegram của bạn vào đây
    ADMIN_IDS = [6513278007]  # Admin ID để quản lý bot
    
    # Cấu hình đăng bài
    DEFAULT_DELAY_BETWEEN_POSTS = int(os.getenv('DEFAULT_DELAY_BETWEEN_POSTS', '2'))  # giây
    MAX_CHANNELS_PER_POST = int(os.getenv('MAX_CHANNELS_PER_POST', '50'))
    
    # Cấu hình scheduler
    SCHEDULER_CHECK_INTERVAL = int(os.getenv('SCHEDULER_CHECK_INTERVAL', '30'))  # giây
    AUTO_CLEANUP_DAYS = int(os.getenv('AUTO_CLEANUP_DAYS', '30'))  # ngày
    
    # Cấu hình file
    CHANNELS_DB_FILE = os.getenv('CHANNELS_DB_FILE', 'channels.json')
    POSTS_DB_FILE = os.getenv('POSTS_DB_FILE', 'posts.json')
    SCHEDULED_POSTS_DB_FILE = os.getenv('SCHEDULED_POSTS_DB_FILE', 'scheduled_posts.json')
    
    # Cấu hình backup
    ENABLE_AUTO_BACKUP = os.getenv('ENABLE_AUTO_BACKUP', 'true').lower() == 'true'
    BACKUP_INTERVAL_HOURS = int(os.getenv('BACKUP_INTERVAL_HOURS', '24'))
    
    # Cấu hình Telegram
    PARSE_MODE_DEFAULT = os.getenv('PARSE_MODE_DEFAULT', 'Markdown')
    DISABLE_WEB_PAGE_PREVIEW = os.getenv('DISABLE_WEB_PAGE_PREVIEW', 'false').lower() == 'true'
    
    # Tin nhắn hệ thống
    WELCOME_MESSAGE = """
🚀 **Chào mừng đến với Bot Đăng Bài Hàng Loạt!**

📢 **Chức năng chính:**
• Đăng bài lên nhiều kênh cùng lúc
• Quản lý danh sách kênh Telegram
• Lên lịch đăng bài tự động
• Thống kê hiệu quả đăng bài
• Hỗ trợ text, hình ảnh, video, file

🎛️ **Bắt đầu:**
Gõ /admin để mở bảng điều khiển chính

💡 **Lưu ý:**
Bot phải là admin trong kênh mới có thể đăng bài
    """
    
    # Thông báo lỗi
    ERROR_MESSAGES = {
        'not_admin': '❌ Bạn không có quyền sử dụng bot này!',
        'bot_not_admin': '❌ Bot không có quyền admin trong kênh này!',
        'channel_not_found': '❌ Không tìm thấy kênh!',
        'channel_exists': '❌ Kênh đã được thêm rồi!',
        'no_channels': '❌ Chưa có kênh nào! Vui lòng thêm kênh trước.',
        'invalid_time': '❌ Thời gian không hợp lệ!',
        'post_failed': '❌ Không thể đăng bài!',
        'schedule_failed': '❌ Không thể lên lịch đăng bài!',
        'operation_cancelled': '✅ Đã hủy thao tác!',
        'no_content': '❌ Vui lòng gửi nội dung bài đăng!',
        'file_too_large': '❌ File quá lớn!',
        'unsupported_file': '❌ Loại file không được hỗ trợ!'
    }
    
    # Thông báo thành công
    SUCCESS_MESSAGES = {
        'channel_added': '✅ Đã thêm kênh thành công!',
        'channel_removed': '✅ Đã xóa kênh thành công!',
        'post_sent': '✅ Đã đăng bài thành công!',
        'post_scheduled': '✅ Đã lên lịch đăng bài thành công!',
        'schedule_cancelled': '✅ Đã hủy lịch đăng bài!',
        'data_exported': '✅ Đã xuất dữ liệu thành công!',
        'cleanup_completed': '✅ Đã dọn dẹp dữ liệu hoàn thành!'
    }
    
    # Cấu hình giới hạn
    LIMITS = {
        'max_text_length': 4096,
        'max_caption_length': 1024,
        'max_channels_per_batch': 20,
        'max_media_group_size': 10,
        'max_file_size_mb': 50,
        'max_scheduled_posts': 100,
        'rate_limit_per_minute': 30
    }
    
    # Các loại file được hỗ trợ
    SUPPORTED_FILE_TYPES = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        'video': ['.mp4', '.mov', '.avi', '.mkv', '.webm'],
        'document': ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar'],
        'audio': ['.mp3', '.wav', '.ogg', '.m4a']
    }
    
    # Danh sách từ cấm
    BANNED_WORDS = [
        "spam",
        "scam",
        "lừa đảo",
        "bán dâm",
        "xxx",
        # ... các từ cấm khác
    ]
    # Cấu hình thời gian
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Ho_Chi_Minh')
    
    # Cấu hình logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
    
    # API limits
    TELEGRAM_API_LIMITS = {
        'messages_per_second': 30,
        'messages_per_minute': 20,
        'bulk_messages_per_minute': 1  # cho group messaging
    }

    # ID nhóm Telegram chính để dashboard quản lý
    MANAGED_GROUP_ID = int(os.getenv('MANAGED_GROUP_ID', '0')) 
    BUTTON_CREATOR_URL = "https://kf-miniapp.ngrok.io/"  # URL mini app tạo nút (local) 