# -*- coding: utf-8 -*-
# (Dòng trống cuối file, chuẩn hóa thụt lề)
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
import pathlib

from telegram import (
    Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InputMediaPhoto, InputMediaVideo, InputMediaDocument, WebAppInfo
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.error import BadRequest, Forbidden

from config import Config
from channel_manager import ChannelManager
from post_manager import PostManager
from scheduler import PostScheduler
from settings_manager import SettingsManager
from language_manager import LanguageManager, Language, get_text
from analytics_manager import AnalyticsManager
from ai_assistant import AIAssistant, get_content_suggestions, check_spam_content

# Cấu hình logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Khắc phục lỗi event loop trên Windows khi dùng Python 3.11+
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# pyright: reportOptionalMemberAccess=false, reportAttributeAccessIssue=false, reportCallIssue=false
class MassPostBot:
    # --- Mẫu bài đăng (Template) ---
    def _load_templates(self):
        path = pathlib.Path("post_templates.json")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_templates(self, templates):
        with open("post_templates.json", "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)

    async def show_templates(self, update):
        templates = self._load_templates()
        if not templates:
            await update.message.reply_text("⚠️ Chưa có mẫu bài đăng nào.")
            return
        keyboard = [[InlineKeyboardButton(t['name'], callback_data=f"use_template_{i}")] for i, t in enumerate(templates)]
        keyboard.append([InlineKeyboardButton("➕ Tạo mẫu mới", callback_data="add_template")])
        await update.message.reply_text("📋 Chọn mẫu bài đăng:", reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_template_callback(self, query, data):
        if data == "add_template":
            await query.edit_message_text("✏️ Gửi nội dung mẫu bài đăng (text/media)")
            user_id = query.from_user.id
            self.user_states[user_id] = {'action': 'adding_template', 'step': 'waiting_content'}
        elif data.startswith("use_template_"):
            idx = int(data.replace("use_template_", ""))
            templates = self._load_templates()
            if 0 <= idx < len(templates):
                template = templates[idx]
                user_id = query.from_user.id
                self.user_states[user_id] = {
                    'action': 'creating_post',
                    'step': 'waiting_content',
                    'post_data': template['content'],
                    'settings': {}
                }
                await query.edit_message_text("✅ Đã chọn mẫu. Gửi nội dung bổ sung hoặc nhấn tiếp tục.")

    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Hiển thị menu chọn ngôn ngữ cho bot
        if not update.message:
            return
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
        keyboard = [
            [
                InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="set_lang_vi"),
                InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
                InlineKeyboardButton("🇨🇳 中文", callback_data="set_lang_zh")
            ]
        ]
        await update.message.reply_text(
            "🌐 Chọn ngôn ngữ cho bot:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_set_language(self, query, data: str):
        # Xử lý chọn ngôn ngữ từ callback
        user_id = query.from_user.id
        if data == "set_lang_vi":
            lang = "vi"
            text = "Đã chuyển ngôn ngữ bot thành Tiếng Việt."
        elif data == "set_lang_en":
            lang = "en"
            text = "Bot language changed to English."
        elif data == "set_lang_zh":
            lang = "zh"
            text = "已切换为中文。"
        else:
            lang = "vi"
            text = "Đã chuyển ngôn ngữ bot thành Tiếng Việt."
        self.user_states.setdefault(user_id, {})['language'] = lang
        await query.edit_message_text(text)
    async def delete_saved_button(self, query, idx: int):
        """Xóa nút đã lưu theo chỉ số idx"""
        if 0 <= idx < len(self.saved_buttons):
            removed = self.saved_buttons.pop(idx)
            self._save_saved_buttons()
            await query.answer(f"✅ Đã xóa nút đã lưu #{idx+1}", show_alert=True)
        else:
            await query.answer("❌ Không tìm thấy nút để xóa!", show_alert=True)

    def _save_saved_buttons(self):
        """Lưu lại danh sách nút đã lưu vào file"""
        import json
        with open(self._saved_buttons_file, "w", encoding="utf-8") as f:
            json.dump(self.saved_buttons, f, ensure_ascii=False, indent=2)
    """Bot đăng bài hàng loạt lên nhiều kênh Telegram"""
    # (End of file. All indentation errors and trailing indented lines have been removed.)
    def __init__(self, token: str, application: Optional[Application] = None):
        self.token = token
        # Đảm bảo bot ở chế độ polling, xoá webhook cũ nếu có
        try:
            asyncio.run(Bot(token).delete_webhook(drop_pending_updates=True))
        except Exception:
            pass  # Bỏ qua lỗi nếu chưa từng thiết lập webhook

        # Sau khi asyncio.run đóng loop, tạo loop mới nếu cần
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        # Dùng Application chung nếu có, tránh tạo mới
        self.application = application if application else Application.builder().token(token).build()
        
        # Khởi tạo các module
        self.channel_manager = ChannelManager()
        self.post_manager = PostManager()
        self.scheduler = PostScheduler(bot=self.application.bot)
        # Đảm bảo scheduler có bot instance
        # self.scheduler.set_bot(self.application.bot)  # không cần vì truyền trong ctor
        self.settings_manager = SettingsManager()
        self.language_manager = LanguageManager()
        self.analytics_manager = AnalyticsManager()
        self.ai_assistant = AIAssistant()
        
        # Trạng thái người dùng
        self.user_states: Dict[int, Dict] = {}
        
        # Bộ nút đã lưu
        self._saved_buttons_file = pathlib.Path("saved_buttons.json")
        self.saved_buttons: List[List[Dict[str, str]]] = self._load_saved_buttons()
        
        # Thiết lập handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        """Thiết lập các handlers cho bot"""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("admin", self.admin_panel))
        self.application.add_handler(CommandHandler("channels", self.show_channels))
        self.application.add_handler(CommandHandler("add_channel", self.add_channel))
        self.application.add_handler(CommandHandler("post", self.create_post))
        self.application.add_handler(CommandHandler("stats", self.show_stats))
        self.application.add_handler(CommandHandler("cancel", self.cancel_flow))
        self.application.add_handler(CommandHandler("schedules", self.list_schedules))
        self.application.add_handler(CommandHandler("language", self.language_command))
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handlers
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
        
        # Nhận dữ liệu trả về từ WebApp
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.handle_webapp_data))
        
        # Debug: Log tất cả message để debug WebApp (đặt ở cuối để không conflict)
        # self.application.add_handler(MessageHandler(filters.ALL, self.debug_all_messages))
        
        # Media handlers
        self.application.add_handler(MessageHandler(
            filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.AUDIO,
            self.handle_media
        ))
    
    def check_user_and_admin(self, update_or_query) -> Optional[int]:
        """Kiểm tra user và admin, trả về user_id hoặc None"""
        if not update_or_query.effective_user:
            return None
        return update_or_query.effective_user.id
    
    async def is_admin(self, user_id: int) -> bool:
        """Kiểm tra user có phải admin không"""
        return user_id in Config.ADMIN_IDS
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lệnh /start"""
        if not update.message:
            return
        
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
        
        # Lấy ngôn ngữ người dùng
        lang_code = self.user_states.get(user_id, {}).get('language', 'vi')
        from language_manager import Language
        welcome_text = self.language_manager.get_text('welcome', Language(lang_code))
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Lệnh /help
        if not update.message:
            return
        help_text = """
🤖 **Hướng dẫn sử dụng Bot Đăng Bài Hàng Loạt**

**📋 Lệnh chính:**
/start - Khởi động bot
/admin - Bảng điều khiển admin
/channels - Xem danh sách kênh
/add_channel - Thêm kênh mới
/post - Tạo bài đăng mới
/stats - Thống kê bot

**🎯 Quy trình sử dụng:**
1. Thêm kênh: /add_channel @channel_name
2. Tạo bài đăng: /post
3. Chọn kênh và gửi
4. Theo dõi thống kê: /stats

**💡 Mẹo:**
- Bot phải là admin trong kênh
- Có thể đăng text, hình ảnh, video
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bảng điều khiển admin"""
        if not update.message:
            return

        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return

        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        # Lấy thống kê
        channels = await self.channel_manager.get_all_channels()
        scheduled_posts = await self.scheduler.get_scheduled_count()
        
        keyboard = [
            [
                InlineKeyboardButton("📢 Đăng bài ngay", callback_data="quick_post"),
                InlineKeyboardButton("⏰ Lên lịch đăng", callback_data="schedule_post")
            ],
            [
                InlineKeyboardButton("📋 Quản lý kênh", callback_data="manage_channels"),
                InlineKeyboardButton("📊 Thống kê chi tiết", callback_data="show_stats")
            ],
            [
                InlineKeyboardButton("📝 Lịch sử đăng", callback_data="post_history"),
                InlineKeyboardButton("⚙️ Cài đặt", callback_data="settings")
            ],
            [
                InlineKeyboardButton("🌐 Ngôn ngữ", callback_data="show_language_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        stats_text = f"""
🤖 **Bảng Điều Khiển Bot**

📊 **Thống kê:**
• Kênh: {len(channels)}
• Bài đăng đã lên lịch: {scheduled_posts}
• Trạng thái: Hoạt động

⚡ **Chọn chức năng:**
        """
        
        await update.message.reply_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_admin_panel(self, query):
        """Hiển thị bảng điều khiển admin trong callback"""
        channels = await self.channel_manager.get_all_channels()
        scheduled_posts = await self.scheduler.get_scheduled_count()

        keyboard = [
            [
                InlineKeyboardButton("📢 Đăng bài ngay", callback_data="quick_post"),
                InlineKeyboardButton("⏰ Lên lịch đăng", callback_data="schedule_post")
            ],
            [
                InlineKeyboardButton("📋 Quản lý kênh", callback_data="manage_channels"),
                InlineKeyboardButton("📊 Thống kê chi tiết", callback_data="show_stats")
            ],
            [
                InlineKeyboardButton("📝 Lịch sử đăng", callback_data="post_history"),
                InlineKeyboardButton("⚙️ Cài đặt", callback_data="settings")
            ],
            [
                InlineKeyboardButton("🌐 Ngôn ngữ", callback_data="show_language_menu")
            ]
        ]

        stats_text = f"""
🤖 **Bảng Điều Khiển Bot**

📊 **Thống kê:**
• Kênh: {len(channels)}
• Bài đăng đã lên lịch: {scheduled_posts}
• Trạng thái: Hoạt động

⚡ **Chọn chức năng:**
        """

        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if data == "show_language_menu":
            await self.language_command(query, context)
        # Xử lý callback từ inline keyboard
        query = update.callback_query
        if not query:
            return

        await query.answer()

        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return

        if not await self.is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền sử dụng này!")
            return

        # Đảm bảo data luôn được gán giá trị hợp lệ
        data = getattr(query, 'data', None)
        if not data:
            return

        if isinstance(data, str) and data.startswith("delete_saved_btn_"):
            try:
                idx = int(data.replace("delete_saved_btn_", ""))
                await self.delete_saved_button(query, idx)
            except Exception:
                await query.answer("❌ Lỗi khi xóa nút đã lưu!", show_alert=True)
            return

        if data in ["set_lang_vi", "set_lang_en", "set_lang_zh"]:
            await self.handle_set_language(query, data)
        elif data == "quick_post":
            # Khởi tạo state cài đặt bài đăng (mặc định)
            user_id = query.from_user.id
            self.user_states[user_id] = {
                'action': 'quick_post_setup',
                'settings': {
                    'notify': True,           # Gửi với thông báo
                    'preview': True,          # Hiển thị preview link
                    'format': 'telegram',     # parse_mode Telegram/HTML
                    'protect': False          # Không bảo vệ nội dung
                }
            }
            # Hiển thị UI
            await self.show_quick_post_intro(query)
        elif data == "quick_post_next":
            # Chuyển sang bước gửi nội dung bài đăng (cho phép mọi loại media)
            await self.start_quick_post_any(query)
        elif data == "schedule_post":
            await self.start_schedule_flow(query)
        # ---------- Quick post setting toggles ----------
        elif data.startswith("quick_setting_toggle_"):
            await self.toggle_quick_setting(query, data)
        elif data.startswith("quick_setting_info_"):
            await self.info_quick_setting(query, data)
        elif data == "create_buttons_help":
            await self.show_button_help(query)
        elif data == "add_buttons_manual":
            await self.prompt_manual_buttons(query)
        elif data == "skip_add_buttons":
            await self.handle_skip_add_buttons(query)
        elif data.startswith("schedule_date_"):
            await self.handle_schedule_date(query, data)
        elif data.startswith("schedule_hour_"):
            await self.handle_schedule_hour(query, data)
        elif data.startswith("schedule_min_"):
            await self.handle_schedule_minute(query, data)
        elif data == "schedule_skip_hour":
            await self.handle_schedule_skip_hour(query)
        elif data == "schedule_skip_min":
            await self.handle_schedule_skip_minute(query)
        elif data == "schedule_back_date":
            await self.show_date_keyboard(query)
        elif data == "schedule_back_hour":
            await self.show_hour_keyboard(query)
        elif data == "manage_channels":
            await self.show_manage_channels(query)
        elif data == "show_stats":
            await self.show_detailed_stats(query)
        elif data == "post_history":
            await self.show_post_history(query)
        elif data == "settings":
            await self.show_settings(query)
        elif data.startswith("add_channel_"):
            await self.handle_add_channel(query, data)
        elif data == "back_main":
            await self.show_admin_panel(query)
        elif data == "back_to_previous":
            await self.handle_back_to_previous(query)
        elif data == "back_manage_channels":
            await self.show_manage_channels(query)
        elif data == "create_text_post":
            # Khởi động quy trình đăng bài text nhanh
            await self.start_quick_text_post(query)
        elif data.startswith("select_channel_"):
            await self.handle_select_channel(query, data)
        elif data == "select_channels_done":
            await self.handle_channels_done(query)
        elif data == "post_to_all":
            if hasattr(self, "handle_post_to_channels"):
                await self.handle_post_to_channels(query, data)
        elif data == "cancel_post":
            await self.cancel_post(query)
        elif data == "create_photo_post":
            await self.start_quick_post(query, media_type="photo")
        elif data == "create_video_post":
            await self.start_quick_post(query, media_type="video")
        elif data == "create_file_post":
            await self.start_quick_post(query, media_type="document")
        elif data == "add_channel_prompt":
            await self.prompt_add_channel(query)
        elif data == "remove_channel_prompt":
            await self.prompt_remove_channel(query)
        elif data.startswith("remove_channel_"):
            await self.confirm_remove_channel(query, data)
        elif data.startswith("cancel_schedule_"):
            await self.handle_cancel_schedule(query, data)
        elif data == "cancel_all_schedules":
            await self.handle_cancel_all_schedules(query)
        elif data == "saved_buttons":
            await self.show_saved_buttons(query)
        elif data.startswith("channels_page_"):
            page = int(data.replace("channels_page_", ""))
            await self.show_manage_channels(query, page)
        elif data.startswith("toggle_channel_"):
            ch_id = data.replace("toggle_channel_", "")
            await self.channel_manager.toggle_channel_status(ch_id)
            await self.show_manage_channels(query)
        elif data.startswith("use_saved_btn_"):
            try:
                idx = int(data.replace("use_saved_btn_", ""))
                if 0 <= idx < len(self.saved_buttons):
                    user_id = query.from_user.id
                    state = self.user_states.get(user_id)
                    # Nếu chưa có state tạo bài đăng, khởi tạo mới
                    if not state or state.get('action') != 'creating_post':
                        self.user_states[user_id] = {
                            'action': 'creating_post',
                            'step': 'adding_buttons',
                            'post_data': {},
                            'settings': {}
                        }
                        state = self.user_states[user_id]
                    # Gắn bộ nút vào post_data
                    state.setdefault('post_data', {})['buttons'] = self.saved_buttons[idx]
                    print(f"DEBUG: Using saved buttons {idx}: {self.saved_buttons[idx]}")  # Debug
                    await query.answer("✅ Đã áp dụng nút đã lưu!")
                    # Gửi lại bài đăng kèm nút cho người dùng kiểm tra
                    post = state['post_data']
                    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(b['text'], url=b['url'])] for b in self.saved_buttons[idx]])
                    # Gửi lại bài đăng kèm nút cho người dùng kiểm tra (trước), sau đó mới gửi menu chọn kênh
                    try:
                        if post.get('type') == 'text':
                            await query.message.reply_text(post.get('text', ''), reply_markup=reply_markup, disable_web_page_preview=True)
                        elif post.get('type') == 'photo':
                            await query.message.reply_photo(post.get('photo'), caption=post.get('caption'), reply_markup=reply_markup)
                        elif post.get('type') == 'video':
                            await query.message.reply_video(post.get('video'), caption=post.get('caption'), reply_markup=reply_markup)
                        elif post.get('type') == 'document':
                            await query.message.reply_document(post.get('document'), caption=post.get('caption'), reply_markup=reply_markup)
                        elif post.get('type') == 'audio':
                            await query.message.reply_audio(post.get('audio'), caption=post.get('caption'), reply_markup=reply_markup)
                        else:
                            preview_text = f"**📋 Preview bài đăng với nút:**\n\nChưa có nội dung bài đăng. Hãy nhập nội dung sau khi chọn nút.\n\n**Nút đã thêm:** {len(self.saved_buttons[idx])}"
                            await query.message.reply_text(preview_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                    except Exception:
                        pass
                    # Chuyển sang bước chọn kênh
                    state['step'] = 'selecting_channels'
                    # Gửi menu chọn kênh ngay sau tin nhắn preview
                    await self.show_channel_selection(query.message, None)
            except (ValueError, IndexError):
                await query.answer("❌ Lỗi khi áp dụng nút!")
        elif data.startswith("channel_stats_"):
            channel_id = data.replace("channel_stats_", "")
            await self.show_channel_stats(query, channel_id)
        elif data.startswith("channel_permissions_"):
            channel_id = data.replace("channel_permissions_", "")
            await self.check_channel_permissions_ui(query, channel_id)
        elif data == "channel_search":
            await self.show_channel_search(query)
        elif data == "bulk_channel_actions":
            await self.show_bulk_channel_actions(query)
        elif data == "channel_backup":
            await self.show_channel_backup_options(query)
        elif data.startswith("toggle_all_channels_"):
            action = data.replace("toggle_all_channels_", "")
            await self.handle_bulk_toggle(query, action == "on")
        elif data == "cleanup_inactive_channels":
            await self.handle_cleanup_inactive(query)
        elif data == "export_channel_stats":
            await self.handle_export_stats(query)
        elif data == "export_channels":
            await self.handle_export_channels(query)
        elif data == "import_channels":
            await self.handle_import_channels(query)
        elif data.startswith("history_page_"):
            page = int(data.replace("history_page_", ""))
            await self.show_post_history(query, page)
        elif data == "history_detailed_stats":
            await self.show_post_detailed_stats(query)
        elif data == "history_filters":
            await self.show_post_history_filters(query)
        elif data == "history_cleanup":
            await self.show_post_cleanup_options(query)
        elif data == "history_export":
            await self.handle_post_history_export(query)
        elif data.startswith("post_detail_"):
            post_id = data.replace("post_detail_", "")
            await self.show_post_detail(query, post_id)
        elif data.startswith("settings_"):
            await self.handle_settings_callback(query, data)
        else:
            # Phản hồi mặc định nếu chưa được hỗ trợ
            await query.answer("🚧 Tính năng đang phát triển!", show_alert=False)
    
    async def show_quick_post(self, query):
        """Hiển thị menu đăng bài nhanh"""
        keyboard = [
            [
                InlineKeyboardButton("📝 Tạo bài text", callback_data="create_text_post"),
                InlineKeyboardButton("📷 Tạo bài có ảnh", callback_data="create_photo_post")
            ],
            [
                InlineKeyboardButton("🎬 Tạo bài video", callback_data="create_video_post"),
                InlineKeyboardButton("📄 Tạo bài file", callback_data="create_file_post")
            ],
            [
                InlineKeyboardButton("🔄 Quay lại", callback_data="back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📢 **Đăng bài nhanh**\n\nChọn loại bài đăng:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_quick_post_intro(self, query):
        """Hiển thị phần giới thiệu gửi bài với các nút tuỳ chỉnh (theo yêu cầu)"""
        user_id = query.from_user.id
        settings = self.user_states.get(user_id, {}).get('settings', {})

        intro_text = (
            "📨 **Gửi bài đăng**\n\n"
            "Trong menu này, bạn có thể chọn **Cài đặt Tweet**\n\n"
            "• Nhấn **nút bên trái** để tìm hiểu cách thức hoạt động của các cài đặt khác nhau.\n\n"
            "• Nhấn **nút bên phải** để thay đổi từng cài đặt: tuỳ chọn được chọn là tuỳ chọn được hiển thị."
        )
        # Helper biểu tượng theo trạng thái
        def on_off_icon(val: bool):
            return "✅ Có" if val else "❌ Không"

        notify_label = on_off_icon(settings.get('notify', True))
        preview_label = on_off_icon(settings.get('preview', True))
        format_label = "🔵 Telegram" if settings.get('format', 'telegram') == 'telegram' else "📄 HTML"
        protect_label = on_off_icon(settings.get('protect', False))

        keyboard = [
            [InlineKeyboardButton("➡️ Tiếp theo", callback_data="quick_post_next")],
            [
                InlineKeyboardButton("🔔 Thông báo", callback_data="quick_setting_info_notify"),
                InlineKeyboardButton(notify_label, callback_data="quick_setting_toggle_notify")
            ],
            [
                InlineKeyboardButton("🔗 Xem trước liên kết", callback_data="quick_setting_info_preview"),
                InlineKeyboardButton(preview_label, callback_data="quick_setting_toggle_preview")
            ],
            [
                InlineKeyboardButton("📝 Định dạng", callback_data="quick_setting_info_format"),
                InlineKeyboardButton(format_label, callback_data="quick_setting_toggle_format")
            ],
            [
                InlineKeyboardButton("🔒 Bảo vệ", callback_data="quick_setting_info_protect"),
                InlineKeyboardButton(protect_label, callback_data="quick_setting_toggle_protect")
            ],
            [
                InlineKeyboardButton("🏠 Menu", callback_data="back_main"),
                InlineKeyboardButton("🔙 Quay lại", callback_data="quick_post")
            ]
        ]
        await self.safe_edit_message(
            query,
            intro_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    # ---------- Quick setting helpers ----------

    async def toggle_quick_setting(self, query, data: str):
        """Bật/tắt tuỳ chọn và refresh UI"""
        user_id = query.from_user.id
        state = self.user_states.get(user_id, {})
        settings = state.setdefault('settings', {})

        key = data.replace("quick_setting_toggle_", "")
        if key == 'format':
            # Vòng qua telegram -> html -> telegram
            settings['format'] = 'html' if settings.get('format', 'telegram') == 'telegram' else 'telegram'
        else:
            current = settings.get(key, False)
            settings[key] = not current

        await self.show_quick_post_intro(query)

    async def info_quick_setting(self, query, data: str):
        """Hiển thị mô tả ngắn cho tuỳ chọn"""
        key = data.replace("quick_setting_info_", "")
        info_map = {
            'notify': "Bật để người dùng kênh nhận thông báo đẩy khi bài đăng được gửi.",
            'preview': "Bật để Telegram hiển thị ảnh xem trước của liên kết (nếu có) trong bài đăng.",
            'format': "Chọn kiểu định dạng văn bản: Telegram (MarkdownV2) hoặc HTML.",
            'protect': "Bật để bảo vệ nội dung (ngăn chuyển tiếp và lưu)."
        }
        await query.answer(info_map.get(key, "Đang phát triển"), show_alert=True)
    
    async def show_manage_channels(self, query, page: int = 0):
        """Hiển thị quản lý kênh với phân trang và tính năng mới"""
        all_channels = await self.channel_manager.get_all_channels()

        per_page = 6  # Giảm để có chỗ cho buttons mới
        total_pages = max(1, (len(all_channels) + per_page - 1) // per_page)
        page = max(0, min(page, total_pages - 1))

        start = page * per_page
        page_channels = all_channels[start:start + per_page]
        
        # Menu top với các tính năng chính
        keyboard = [
            [
            InlineKeyboardButton("➕ Thêm kênh", callback_data="add_channel_prompt"),
            InlineKeyboardButton("🗑️ Xóa kênh", callback_data="remove_channel_prompt")
            ],
            [
                InlineKeyboardButton("🔍 Tìm kiếm", callback_data="channel_search"),
                InlineKeyboardButton("📊 Thống kê tổng", callback_data="show_stats")
            ],
            [
                InlineKeyboardButton("⚡ Hành động hàng loạt", callback_data="bulk_channel_actions"),
                InlineKeyboardButton("💾 Sao lưu", callback_data="channel_backup")
            ]
        ]

        # Danh sách kênh với thống kê và quyền
        for ch in page_channels:
            ch_id = str(ch.get('id'))
            active = ch.get('active', True)
            prefix = "✅" if active else "🚫"
            name = ch.get('title', ch.get('name', ch_id))[:25]  # Giới hạn độ dài
            
            # Thêm thống kê ngắn
            post_count = ch.get('post_count', 0)
            success_rate = 0
            if post_count > 0:
                success_count = ch.get('success_count', 0)
                success_rate = int(success_count / post_count * 100)
            
            # Row cho toggle status
            keyboard.append([
                InlineKeyboardButton(f"{prefix} {name} ({post_count} bài, {success_rate}%)", 
                                   callback_data=f"toggle_channel_{ch_id}")
            ])
        
            # Row cho stats và permissions
        keyboard.append([
                InlineKeyboardButton("📊 Thống kê", callback_data=f"channel_stats_{ch_id}"),
                InlineKeyboardButton("🔑 Quyền", callback_data=f"channel_permissions_{ch_id}")
            ])

        # Pagination row
        nav_row = []
        if total_pages > 1:
            if page > 0:
                nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"channels_page_{page-1}"))
            nav_row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
            if page < total_pages - 1:
                nav_row.append(InlineKeyboardButton("➡️", callback_data=f"channels_page_{page+1}"))
        if nav_row:
            keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")])

        active_count = len([c for c in all_channels if c.get('active', True)])
        total_posts = sum(c.get('post_count', 0) for c in all_channels)
        
        text = (
            f"📢 **Quản lý kênh** ({len(all_channels)} kênh)\n\n"
            f"✅ Hoạt động: {active_count}\n"
            f"🚫 Tắt: {len(all_channels) - active_count}\n"
            f"📊 Tổng bài đăng: {total_posts}\n\n"
            f"Chọn kênh để bật/tắt hoặc sử dụng các tính năng bên dưới:"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_detailed_stats(self, query):
        """Hiển thị thống kê chi tiết"""
        # Lấy thống kê từ các module
        channels = await self.channel_manager.get_all_channels()
        total_posts = await self.post_manager.get_total_posts()
        scheduled_count = await self.scheduler.get_scheduled_count()
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Xuất báo cáo", callback_data="export_report"),
                InlineKeyboardButton("🔄 Refresh", callback_data="show_stats")
            ],
            [
                InlineKeyboardButton("🔄 Quay lại", callback_data="back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        stats_text = f"""
📊 **Thống kê chi tiết**

📢 **Kênh:**
• Tổng số: {len(channels)}
• Hoạt động: {len([c for c in channels if c.get('active', True)])}
• Không hoạt động: {len([c for c in channels if not c.get('active', True)])}

📝 **Bài đăng:**
• Tổng đã đăng: {total_posts}
• Đang chờ lịch: {scheduled_count}

⏰ **Hôm nay:**
• Cập nhật: {datetime.now().strftime('%H:%M %d/%m/%Y')}
        """
        
        await query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị danh sách kênh"""
        if not update.message:
            return
        
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
            
        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        channels = await self.channel_manager.get_all_channels()
        
        if not channels:
            keyboard = [
                [InlineKeyboardButton("➕ Thêm kênh", callback_data="add_channel_prompt")],
                [InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]
            ]
            await update.message.reply_text(
                "📋 **Danh sách kênh trống**\n\n💡 Sử dụng nút 'Thêm kênh' để thêm kênh mới.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        channel_text = "📋 **Danh sách kênh:**\n\n"
        for i, info in enumerate(channels, 1):
            channel_id = info.get('id')
            status = "✅" if info.get('active', True) else "🚫"
            name = info.get('name') or info.get('title') or channel_id
            username = f"@{info.get('username')}" if info.get('username') else "Không có"
            post_count = info.get('post_count', 0)
            
            channel_text += (
                f"{i}. {status} **{name}**\n"
                f"   🆔 ID: `{channel_id}`\n"
                f"   📢 Username: {username}\n"
                f"   📊 Bài đăng: {post_count}\n\n"
            )
        
        # Thêm keyboard với các hành động
        keyboard = [
            [
                InlineKeyboardButton("📋 Quản lý kênh", callback_data="manage_channels"),
                InlineKeyboardButton("➕ Thêm kênh", callback_data="add_channel_prompt")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]
        ]
        
        await update.message.reply_text(
            channel_text, 
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Thêm kênh mới"""
        if not update.message:
            return
        
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
            
        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 **Thêm kênh mới**\n\n"
                "Sử dụng: `/add_channel @channel_name`\n"
                "Hoặc: `/add_channel -1001234567890`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        channel_input = context.args[0]
        
        try:
            result = await self.channel_manager.add_channel(channel_input, context.bot)
            if result['success']:
                await update.message.reply_text(
                    f"✅ **Đã thêm kênh thành công!**\n\n"
                    f"📢 Kênh: {result['channel_name']}\n"
                    f"🆔 ID: `{result['channel_id']}`",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    f"❌ **Lỗi khi thêm kênh:**\n{result['error']}",
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Lỗi:** {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def create_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tạo bài đăng mới"""
        if not update.message:
            return
        
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
            
        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        # Giữ lại cài đặt nếu có
        prev_state = self.user_states.get(user_id, {})
        settings = prev_state.get('settings', {})
        self.user_states[user_id] = {
            'action': 'creating_post',
            'step': 'waiting_content',
            'post_data': {},
            'settings': settings
        }
        
        await update.message.reply_text(
            "📝 **Tạo bài đăng mới**\n\n"
            "Gửi nội dung bài đăng (text, ảnh, video, file).\n"
            "Gõ /cancel để hủy.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý tin nhắn text"""
        if not update.message:
            return
        
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
        
        if not await self.is_admin(user_id):
            return
        
        # Kiểm tra trạng thái người dùng
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        
        if state.get('action') == 'creating_post' and state.get('step') == 'waiting_content':
            await self.process_post_content(update, context)
        elif state.get('action') == 'creating_post' and state.get('step') == 'adding_buttons':
            await self.process_add_buttons(update, context)
        elif state.get('action') == 'adding_template' and state.get('step') == 'waiting_content':
            # Lưu mẫu bài đăng
            content = {}
            if update.message.text:
                content = {'type': 'text', 'text': update.message.text}
            elif update.message.photo:
                content = {'type': 'photo', 'photo': update.message.photo[-1].file_id, 'caption': update.message.caption or ''}
            elif update.message.video:
                content = {'type': 'video', 'video': update.message.video.file_id, 'caption': update.message.caption or ''}
            elif update.message.document:
                content = {'type': 'document', 'document': update.message.document.file_id, 'caption': update.message.caption or ''}
            elif update.message.audio:
                content = {'type': 'audio', 'audio': update.message.audio.file_id, 'caption': update.message.caption or ''}
            templates = self._load_templates()
            name = f"Mẫu {len(templates)+1}"
            templates.append({'name': name, 'content': content})
            self._save_templates(templates)
            await update.message.reply_text(f"✅ Đã lưu mẫu bài đăng: {name}")
            self.user_states.pop(user_id, None)
        elif state.get('action') == 'adding_channel' and state.get('step') == 'waiting_channel':
            await self.process_add_channel(update, context)
        elif state.get('action') == 'searching_channel' and state.get('step') == 'waiting_query':
            await self.process_channel_search(update, context)
        elif state.get('action') == 'scheduling_post':
            if state.get('step') == 'waiting_content':
                await self.process_schedule_content(update, context)
            elif state.get('step') == 'waiting_time':
                await self.process_schedule_time(update, context)
            return
        elif state.get('action') == 'setting_input':
            await self.process_setting_input(update, context)
    
    async def handle_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý tin nhắn media"""
        if not update.message:
            return
        
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
        
        if not await self.is_admin(user_id):
            return
        
        # Kiểm tra trạng thái người dùng
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        
        if state.get('action') == 'creating_post' and state.get('step') == 'waiting_content':
            await self.process_post_content(update, context)
        elif state.get('action') == 'creating_post' and state.get('step') == 'adding_buttons':
            await self.process_add_buttons(update, context)
        elif state.get('action') == 'scheduling_post' and state.get('step') == 'waiting_content':
            await self.process_schedule_content(update, context)
    
    async def process_post_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý nội dung bài đăng"""
        if not update.message:
            return
        
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
        
        # Tích hợp AI kiểm duyệt nội dung
        content = {}
        if update.message.text:
            content = {'type': 'text', 'text': update.message.text}
        elif update.message.photo:
            content = {'type': 'photo', 'photo': update.message.photo[-1].file_id, 'caption': update.message.caption or ''}
        elif update.message.video:
            content = {'type': 'video', 'video': update.message.video.file_id, 'caption': update.message.caption or ''}
        elif update.message.document:
            content = {'type': 'document', 'document': update.message.document.file_id, 'caption': update.message.caption or ''}
        elif update.message.audio:
            content = {'type': 'audio', 'audio': update.message.audio.file_id, 'caption': update.message.caption or ''}

        # AI kiểm duyệt nội dung
        ai_result = await self.ai_assistant.check_spam_content(content.get('text', '') if content.get('type') == 'text' else content.get('caption', ''))
        if ai_result.get('is_spam'):
            await update.message.reply_text(f"⚠️ Nội dung bị chặn bởi AI kiểm duyệt: {ai_result.get('reason', 'Nội dung không phù hợp.')}")
            return
        
        # Lưu nội dung
        self.user_states[user_id]['post_data'] = content
        self.user_states[user_id]['step'] = 'adding_buttons'

        # Gửi lại bản xem trước để người dùng đối chiếu
        try:
            if content['type'] == 'text':
                await update.message.reply_text(content['text'], parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            elif content['type'] == 'photo':
                await update.message.reply_photo(content['photo'], caption=content.get('caption'))
            elif content['type'] == 'video':
                await update.message.reply_video(content['video'], caption=content.get('caption'))
            elif content['type'] == 'document':
                await update.message.reply_document(content['document'], caption=content.get('caption'))
            elif content['type'] == 'audio':
                await update.message.reply_audio(content['audio'], caption=content.get('caption'))
        except Exception:
            pass  # Trong trường hợp gửi lỗi, bỏ qua để không chặn flow

        # Hiển thị hướng dẫn tạo nút + bàn phím như mẫu
        guide_text = (
            "🎯 **Hướng dẫn tạo nút dưới bài viết**\n\n"
            "**📝 Cú pháp:** `Tên nút | Link`\n\n"
            "**🔗 Các loại nút được hỗ trợ:**\n"
            "• **Nút liên kết thường:**\n"
            "`Tham gia kênh | https://t.me/example`\n\n"
            "• **Nút mở trang web:**\n"
            "`Website | https://example.com`\n\n"
            "• **Nút liên hệ admin:**\n"
            "`Liên hệ | https://t.me/admin`\n\n"
            "• **Nút kênh riêng tư:**\n"
            "`VIP Channel | https://t.me/+NV5LFI4T7n0yZjUx`\n\n"
            "**📋 Tạo nhiều nút:**\n"
            "• **Nhiều nút (mỗi dòng 1 nút):**\n"
            "```\n"
            "Kênh chính | https://t.me/example\n"
            "Website | https://example.com\n"
            "Liên hệ | https://t.me/admin\n"
            "```\n\n"
            "**⚠️ Lưu ý:** Mỗi dòng chỉ được 1 nút, sử dụng dấu `|` để phân tách tên và link"
        )

        keyboard = [
            [InlineKeyboardButton("📚 Nút đã lưu", callback_data="saved_buttons"), InlineKeyboardButton("✏️ Tạo nút thủ công", callback_data="add_buttons_manual")],
            [InlineKeyboardButton("🚫 Không nút", callback_data="skip_add_buttons")],
            [InlineKeyboardButton("🏠 Menu", callback_data="back_main"), InlineKeyboardButton("🔙 Quay lại", callback_data="back_to_previous")]
        ]

        await update.message.reply_text(
            guide_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def process_add_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý phần nhập nút (button) cho bài đăng rồi chuyển sang bước chọn kênh."""
        if not update.message:
            return

        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return

        state = self.user_states.get(user_id, {})
        if state.get('action') != 'creating_post' or state.get('step') != 'adding_buttons':
            return

        input_text = (update.message.text or '').strip()

        buttons: List[Dict[str, str]] = []

        # Nếu người dùng bỏ qua việc thêm nút
        if input_text.lower() not in ['bỏ qua', 'bo qua', 'skip', 'no', 'không', 'khong', 'none']:
            for line in input_text.splitlines():
                if '|' not in line:
                    # Thông báo lỗi nhẹ nhưng không dừng luồng
                    await update.message.reply_text(f"⚠️ Dòng không hợp lệ (thiếu '|'): {line}")
                    continue
                label, url = line.split('|', 1)
                label = label.strip()
                url = url.strip()
                if not label or not url:
                    await update.message.reply_text(f"⚠️ Dòng không hợp lệ: {line}")
                    continue
                buttons.append({'text': label, 'url': url})

        # Lưu nút vào post_data nếu có
        if buttons:
            state.setdefault('post_data', {})['buttons'] = buttons
            self._add_saved_buttons(buttons)

        # Gửi lại bản xem trước kèm nút để người dùng kiểm tra lần cuối
        post = state.get('post_data', {})
        reply_markup = None
        if post.get('buttons'):
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(btn['text'], url=btn['url'])] for btn in post['buttons']])

        try:
            if post.get('type') == 'text':
                await update.message.reply_text(post.get('text', ''), reply_markup=reply_markup, disable_web_page_preview=True)
            elif post.get('type') == 'photo':
                await update.message.reply_photo(post.get('photo'), caption=post.get('caption'), reply_markup=reply_markup)
            elif post.get('type') == 'video':
                await update.message.reply_video(post.get('video'), caption=post.get('caption'), reply_markup=reply_markup)
            elif post.get('type') == 'document':
                await update.message.reply_document(post.get('document'), caption=post.get('caption'), reply_markup=reply_markup)
            elif post.get('type') == 'audio':
                await update.message.reply_audio(post.get('audio'), caption=post.get('caption'), reply_markup=reply_markup)
        except Exception:
            pass

        # Chuyển sang bước chọn kênh
        state['step'] = 'selecting_channels'
        await self.show_channel_selection(update.message, context)
    
    async def show_channel_selection(self, update_or_query, context, refresh=False):
        """Hiển thị lựa chọn kênh"""
        # update_or_query: có thể là Update (message) hoặc CallbackQuery
        from telegram import CallbackQuery, Message
        if isinstance(update_or_query, CallbackQuery):
            message_sender = update_or_query  # dùng edit_message_text
            user_id = update_or_query.from_user.id
        elif isinstance(update_or_query, Message):
            message_sender = update_or_query
            user_id = update_or_query.from_user.id
        elif hasattr(update_or_query, 'message') and update_or_query.message:
            message_sender = update_or_query.message
            user_id = message_sender.from_user.id
        if user_id is None:
            return
        state = self.user_states.get(user_id, {})
        selected = set(state.get('selected_channels', []))
        
        channels = await self.channel_manager.get_all_channels()
        
        if not channels:
            await message_sender.reply_text(
                "❌ **Chưa có kênh nào!**\n\n"
                "Sử dụng /add_channel để thêm kênh trước.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        keyboard = []
        for channel in channels:
            channel_id = str(channel.get('id'))
            name = channel.get('name') or channel.get('title') or channel_id
            prefix = "✅ " if channel_id in selected else "☑️ "
            keyboard.append([
                InlineKeyboardButton(f"{prefix}{name}", callback_data=f"select_channel_{channel_id}")
            ])
        
        bottom_row = [InlineKeyboardButton("🔙 Quay lại", callback_data="back_to_previous")]
        if state.get('action') == 'creating_post':
            bottom_row.insert(0, InlineKeyboardButton("✅ Gửi", callback_data="select_channels_done"))
        elif state.get('action') == 'scheduling_post':
            bottom_row.insert(0, InlineKeyboardButton("➡️ Tiếp tục", callback_data="select_channels_done"))
        if len(channels) > 1:
            bottom_row.append(InlineKeyboardButton("✅ Gửi tất cả", callback_data="post_to_all"))
        keyboard.append(bottom_row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "📋 **Chọn kênh đăng bài:**\n\n"
        if selected:
            text += f"✅ Đã chọn: {len(selected)} kênh\n"
        text += "Chạm vào kênh để chọn/bỏ chọn, sau đó nhấn Gửi."
        if isinstance(message_sender, Message):
            await message_sender.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        elif hasattr(message_sender, 'edit_message_text'):
            await message_sender.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị thống kê"""
        if not update.message:
            return
        
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
        
        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        channels = await self.channel_manager.get_all_channels()
        total_posts: int = await self.post_manager.get_total_posts()
        scheduled_count: int = await self.scheduler.get_scheduled_count()
        
        active = len([c for c in channels if c.get('active', True)])
        
        stats_text = f"""
📊 **Thống kê Bot**

📢 **Kênh:**
• Tổng số: {len(channels)}
• Hoạt động: {active}

📝 **Bài đăng:**
• Tổng đã đăng: {total_posts}
• Đang chờ lịch: {scheduled_count}

⏰ **Cập nhật:** {datetime.now().strftime('%H:%M %d/%m/%Y')}
        """
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    
    # Các method bổ sung để sửa lỗi type checking
    async def start_schedule_flow(self, query):
        """Bắt đầu luồng lên lịch: hỏi nội dung"""
        user_id = query.from_user.id
        self.user_states[user_id] = {
            'action': 'scheduling_post',
            'step': 'waiting_content',
            'post_data': {}
        }
        await query.edit_message_text(
            "⏰ **Lên lịch đăng bài**\n\nGửi nội dung bài đăng (text / media).\nSau đó bot sẽ hỏi thời gian.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]]),
            parse_mode=ParseMode.MARKDOWN
        )

    # ---------- Scheduler keyboards ----------
    def _get_upcoming_dates(self, days: int = 6):
        today = datetime.now().date()
        return [(today + timedelta(days=i)) for i in range(days)]

    async def show_date_keyboard(self, query):
        dates = self._get_upcoming_dates()
        keyboard = []
        row = []
        for d in dates:
            label = d.strftime("%d/%m")
            row.append(InlineKeyboardButton(label, callback_data=f"schedule_date_{d.strftime('%Y%m%d')}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([
            InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")
        ])
        await query.edit_message_text(
            "📅 **Chọn ngày đăng:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_hour_keyboard(self, query):
        keyboard = []
        row = []
        for h in range(24):
            label = f"{h:02d}"
            row.append(InlineKeyboardButton(label, callback_data=f"schedule_hour_{h:02d}"))
            if len(row) == 6:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([
            InlineKeyboardButton("⬅️ Quay lại", callback_data="schedule_back_date"),
            InlineKeyboardButton("⏭️ Bỏ qua", callback_data="schedule_skip_hour")
        ])
        await query.edit_message_text(
            "🕑 **Chọn giờ (0-23):**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_minute_keyboard(self, query):
        minutes = [0,5,10,15,20,25,30,35,40,45,50,55]
        keyboard = []
        row = []
        for m in minutes:
            label = f"{m:02d}"
            row.append(InlineKeyboardButton(label, callback_data=f"schedule_min_{m:02d}"))
            if len(row) == 4:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([
            InlineKeyboardButton("⬅️ Quay lại", callback_data="schedule_back_hour"),
            InlineKeyboardButton("⏭️ Bỏ qua", callback_data="schedule_skip_min")
        ])
        await query.edit_message_text(
            "⏰ **Chọn phút:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    # ---------- Scheduler handlers ----------

    async def handle_schedule_date(self, query, data: str):
        user_id = query.from_user.id
        state = self.user_states.get(user_id)
        if not state or state.get('action') != 'scheduling_post':
            return
        date_str = data.replace("schedule_date_", "")
        state.setdefault('schedule', {})['date'] = date_str
        state['step'] = 'selecting_hour'
        await self.show_hour_keyboard(query)

    async def handle_schedule_hour(self, query, data: str):
        user_id = query.from_user.id
        state = self.user_states.get(user_id)
        if not state or state.get('action') != 'scheduling_post':
            return
        hour = int(data.replace("schedule_hour_", ""))
        state.setdefault('schedule', {})['hour'] = hour
        state['step'] = 'selecting_min'
        await self.show_minute_keyboard(query)

    async def handle_schedule_minute(self, query, data: str):
        user_id = query.from_user.id
        state = self.user_states.get(user_id)
        if not state or state.get('action') != 'scheduling_post':
            return
        minute = int(data.replace("schedule_min_", ""))
        await self._finalize_schedule(query, state, minute)

    async def handle_schedule_skip_hour(self, query):
        user_id = query.from_user.id
        state = self.user_states.get(user_id)
        if not state:
            return
        state.setdefault('schedule', {})['hour'] = 0
        state['step'] = 'selecting_min'
        await self.show_minute_keyboard(query)

    async def handle_schedule_skip_minute(self, query):
        user_id = query.from_user.id
        state = self.user_states.get(user_id)
        if not state:
            return
        await self._finalize_schedule(query, state, 0)

    async def _finalize_schedule(self, query, state: Dict, minute: int):
        schedule_info = state.get('schedule', {})
        date_str = schedule_info.get('date')
        hour = schedule_info.get('hour', 0)
        if not date_str:
            await query.answer("Thiếu ngày!", show_alert=True)
            return
        schedule_time = datetime.strptime(date_str, "%Y%m%d")
        schedule_time = schedule_time.replace(hour=hour, minute=minute, second=0)
        if schedule_time < datetime.now():
            await query.answer("Thời gian đã qua", show_alert=True)
            return
        post_data: Dict[str, Any] = state.get('post_data', {})
        channels = await self.channel_manager.get_all_channels()
        schedule_id = await self.scheduler.schedule_post(post_data, channels, schedule_time)
        # clear state
        user_id = query.from_user.id
        self.user_states.pop(user_id, None)
        keyboard = [
            [InlineKeyboardButton("⬅️ Quay lại", callback_data="schedule_post"), InlineKeyboardButton("🏠 Menu chính", callback_data="back_main")]
        ]
        await query.edit_message_text(
            f"✅ Đã lên lịch <code>{schedule_id}</code> lúc {schedule_time.strftime('%H:%M %d/%m/%Y')}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    
    async def show_post_history(self, query, page: int = 0):
        """Hiển thị lịch sử đăng bài với phân trang"""
        
        # Lấy dữ liệu từ post_manager
        all_posts = await self.post_manager.get_post_history(limit=100)  # Lấy 100 bài gần nhất
        stats = await self.post_manager.get_statistics()
        
        if not all_posts:
            keyboard = [
                [InlineKeyboardButton("📢 Đăng bài đầu tiên", callback_data="quick_post")],
                [InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]
            ]
            
            await self.safe_edit_message(
                query,
                "📝 **Lịch sử đăng bài**\n\n"
                "📋 Chưa có bài đăng nào!\n\n"
                "💡 Hãy tạo bài đăng đầu tiên của bạn.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Cấu hình phân trang
        per_page = 5
        total_pages = max(1, (len(all_posts) + per_page - 1) // per_page)
        page = max(0, min(page, total_pages - 1))
        
        start = page * per_page
        page_posts = all_posts[start:start + per_page]
        
        # Tạo text hiển thị
        history_text = (
            f"📝 **Lịch sử đăng bài** (Trang {page + 1}/{total_pages})\n\n"
            f"📊 **Thống kê tổng quan:**\n"
            f"• Tổng bài đăng: {stats['total_posts']}\n"
            f"• Thành công: {stats['successful_posts']} ({stats['success_rate']:.1f}%)\n"
            f"• Thất bại: {stats['failed_posts']}\n"
            f"• Hôm nay: {stats['today_posts']} bài\n\n"
            f"📋 **Danh sách bài đăng:**\n"
        )
        
        # Thêm từng bài đăng
        for i, post in enumerate(page_posts, start + 1):
            post_id = post.get('id', 'Unknown')
            post_type = post.get('type', 'text')
            created_at = post.get('created_at', '')
            
            # Format thời gian
            try:
                dt = datetime.fromisoformat(created_at)
                time_str = dt.strftime('%H:%M %d/%m')
            except:
                time_str = 'N/A'
            
            # Icon loại bài đăng  
            type_icons = {
                'text': '📝',
                'photo': '🖼️', 
                'video': '🎥',
                'document': '📄',
                'audio': '🎵'
            }
            type_icon = type_icons.get(post_type, '📝')
            
            # Thống kê kênh
            channels_data = post.get('channels', {})
            total_channels = len(channels_data)
            success_channels = sum(1 for ch in channels_data.values() if ch.get('success', False))
            
            # Preview nội dung
            content_preview = ""
            if post_type == 'text':
                content_preview = (post.get('text', '')[:30] + '...') if len(post.get('text', '')) > 30 else post.get('text', '')
            elif 'caption' in post:
                caption = post.get('caption', '')
                content_preview = (caption[:30] + '...') if len(caption) > 30 else caption
            else:
                content_preview = f"{post_type.title()} file"
            
            history_text += (
                f"`{i}.` {type_icon} **{post_id}**\n"
                f"   📅 {time_str} | 📊 {success_channels}/{total_channels} kênh\n"
                f"   💬 {content_preview}\n\n"
            )
        
        # Tạo keyboard với navigation và actions
        keyboard = []
        
        # Navigation row
        nav_row = []
        if total_pages > 1:
            if page > 0:
                nav_row.append(InlineKeyboardButton("⬅️ Trước", callback_data=f"history_page_{page-1}"))
            nav_row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
            if page < total_pages - 1:
                nav_row.append(InlineKeyboardButton("Sau ➡️", callback_data=f"history_page_{page+1}"))
        if nav_row:
            keyboard.append(nav_row)
        
        # Action rows
        keyboard.extend([
            [
                InlineKeyboardButton("📊 Thống kê chi tiết", callback_data="history_detailed_stats"),
                InlineKeyboardButton("🔍 Bộ lọc", callback_data="history_filters")
            ],
            [
                InlineKeyboardButton("🗑️ Xóa cũ", callback_data="history_cleanup"),
                InlineKeyboardButton("📤 Xuất dữ liệu", callback_data="history_export")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]
        ])
        
        await self.safe_edit_message(
            query,
            history_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_settings(self, query):
        """Hiển thị menu cài đặt chính"""
        # Lấy thông tin phiên bản và cập nhật cuối
        meta = self.settings_manager.get_category("meta")
        last_updated = meta.get("last_updated", "N/A")
        try:
            if last_updated != "N/A":
                dt = datetime.fromisoformat(last_updated)
                last_updated = dt.strftime("%H:%M %d/%m/%Y")
        except:
            last_updated = "N/A"
        
        settings_text = (
            f"⚙️ **Cài đặt Bot**\n\n"
            f"🔧 **Phiên bản:** {meta.get('version', '1.0.0')}\n"
            f"📅 **Cập nhật cuối:** {last_updated}\n"
            f"🔄 **Số lần thay đổi:** {meta.get('update_count', 0)}\n\n"
            f"📋 **Chọn danh mục cài đặt:**"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🤖 Cài đặt Bot", callback_data="settings_bot"),
                InlineKeyboardButton("⏰ Lịch đăng", callback_data="settings_scheduler")
            ],
            [
                InlineKeyboardButton("🔔 Thông báo", callback_data="settings_notifications"),
                InlineKeyboardButton("💾 Backup", callback_data="settings_backup")
            ],
            [
                InlineKeyboardButton("🔒 Bảo mật", callback_data="settings_security"),
                InlineKeyboardButton("🎨 Giao diện", callback_data="settings_interface")
            ],
            [
                InlineKeyboardButton("🔧 Nâng cao", callback_data="settings_advanced"),
                InlineKeyboardButton("📤 Xuất/Nhập", callback_data="settings_export")
            ],
            [
                InlineKeyboardButton("🔄 Reset tất cả", callback_data="settings_reset_all"),
                InlineKeyboardButton("📋 Kiểm tra", callback_data="settings_validate")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]
        ]
        
        await self.safe_edit_message(
            query,
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_add_channel(self, query, data: str):
        """Xử lý thêm kênh - redirect to prompt"""
        await self.prompt_add_channel(query)
    
    async def handle_remove_channel(self, query, data: str):
        """Xử lý callback xoá kênh (remove_channel_<id>)"""
        channel_id = data.replace("remove_channel_", "")
        removed = await self.channel_manager.remove_channel(channel_id)
        if removed:
            text = f"✅ Đã xoá kênh `{channel_id}`"
        else:
            text = "❌ Không tìm thấy kênh hoặc lỗi khi xoá."

        # Sau khi xoá → hiển thị lại menu quản lý kênh
        try:
            await self.show_manage_channels(query)
        except Exception as e:
            # Nếu nội dung không đổi, Telegram sẽ báo lỗi, bỏ qua
            if "Message is not modified" in str(e):
                pass
            else:
                raise
        await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_select_channel(self, query, data: str):
        # Toggle chọn/huỷ chọn kênh trong state rồi refresh keyboard
        user_id = query.from_user.id
        state = self.user_states.get(user_id)
        if not state:
            return
        channel_id = data.replace("select_channel_", "")
        selected: Set[str] = set(state.setdefault('selected_channels', []))
        if channel_id in selected:
            selected.remove(channel_id)
        else:
            selected.add(channel_id)
        state['selected_channels'] = list(selected)
        # Hiển thị lại danh sách kênh với dấu tick
        await self.show_channel_selection(query, None, refresh=True)

    async def handle_channels_done(self, query):
        # Người dùng xác nhận chọn kênh
        user_id = query.from_user.id
        state = self.user_states.get(user_id)
        if not isinstance(state, dict) or not state:
            return
        selected = state.get('selected_channels', [])
        if not selected:
            await query.answer("⚠️ Hãy chọn ít nhất 1 kênh", show_alert=True)
            return
        if state.get('action') == 'creating_post':
            # gửi ngay tới kênh đã chọn
            state['send_channels_override'] = selected
            await self._send_post_to_selected(query, dict(state))
        elif state.get('action') == 'scheduling_post':
            state['channels_selected'] = selected
            state['step'] = 'selecting_date'
            await self.show_date_keyboard(query)

    async def _send_post_to_selected(self, query, state: Dict):
        post = state.get('post_data', {})
        settings = state.get('settings', {})
        channel_ids = state.get('send_channels_override', [])
        sent = 0
        failed: List[str] = []
        
        # Tạo reply_markup từ buttons nếu có
        reply_markup = None
        if post.get('buttons'):
            keyboard = [[InlineKeyboardButton(btn['text'], url=btn['url'])] for btn in post['buttons']]
            reply_markup = InlineKeyboardMarkup(keyboard)
            print(f"DEBUG: Sending with {len(post['buttons'])} buttons")  # Debug

        for ch_id in channel_ids:
            try:
                if post['type'] == 'text':
                    await self.application.bot.send_message(
                        chat_id=ch_id,
                        text=post['text'],
                        disable_web_page_preview=not settings.get('preview', True),
                        disable_notification=not settings.get('notify', True),
                        protect_content=settings.get('protect', False),
            reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML if settings.get('format', 'telegram') == 'html' else ParseMode.MARKDOWN_V2
                    )
                elif post['type'] == 'photo':
                    await self.application.bot.send_photo(
                        chat_id=ch_id,
                        photo=post['photo'],
                        caption=post.get('caption'),
                        disable_notification=not settings.get('notify', True),
                        protect_content=settings.get('protect', False),
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML if settings.get('format', 'telegram') == 'html' else ParseMode.MARKDOWN_V2
                    )
                elif post['type'] == 'video':
                    await self.application.bot.send_video(
                        chat_id=ch_id,
                        video=post['video'],
                        caption=post.get('caption'),
                        disable_notification=not settings.get('notify', True),
                        protect_content=settings.get('protect', False),
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML if settings.get('format', 'telegram') == 'html' else ParseMode.MARKDOWN_V2
                    )
                elif post['type'] == 'document':
                    await self.application.bot.send_document(
                        chat_id=ch_id,
                        document=post['document'],
                        caption=post.get('caption'),
                        disable_notification=not settings.get('notify', True),
                        protect_content=settings.get('protect', False),
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML if settings.get('format', 'telegram') == 'html' else ParseMode.MARKDOWN_V2
                    )
                elif post['type'] == 'audio':
                    await self.application.bot.send_audio(
                        chat_id=ch_id,
                        audio=post['audio'],
                        caption=post.get('caption'),
                        disable_notification=not settings.get('notify', True),
                        protect_content=settings.get('protect', False),
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML if settings.get('format', 'telegram') == 'html' else ParseMode.MARKDOWN_V2
                    )
                sent += 1
            except Exception:
                failed.append(str(ch_id))
        user_id = query.from_user.id
        self.user_states.pop(user_id, None)
        text = f"📤 Đã gửi bài tới {sent}/{len(channel_ids)} kênh."
        if failed:
            text += "\n⚠️ Lỗi ở: " + ", ".join(failed)
        await query.edit_message_text(text)
    
    async def handle_post_to_channels(self, query, data: str):
        """Gửi bài đã soạn tới tất cả kênh"""
        user_id = query.from_user.id
        # Lấy dữ liệu bài viết
        state = self.user_states.get(user_id)
        if not state or not state.get('post_data'):
            await query.edit_message_text("❌ Chưa có nội dung bài đăng!")
            return
        post = state['post_data']
        # Lấy danh sách kênh
        channels = await self.channel_manager.get_all_channels()
        if not channels:
            await query.edit_message_text("❌ Chưa có kênh nào để đăng!")
            return
        sent = 0
        errors = 0
        failed_channels: List[str] = []
        settings = state.get('settings', {})
        reply_markup = None
        if post.get('buttons'):
            keyboard = [[InlineKeyboardButton(btn['text'], url=btn['url'])] for btn in post['buttons']]
            reply_markup = InlineKeyboardMarkup(keyboard)
        for ch in channels:
            channel_id_any = ch.get('id')
            if channel_id_any is None:
                continue
            channel_id = str(channel_id_any)
            try:
                if post['type'] == 'text':
                    await self.application.bot.send_message(
                        chat_id=channel_id,
                        text=post['text'],
                        disable_web_page_preview=not settings.get('preview', True),
                        disable_notification=not settings.get('notify', True),
                        protect_content=settings.get('protect', False),
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML if settings.get('format', 'telegram') == 'html' else ParseMode.MARKDOWN_V2
                    )
                elif post['type'] == 'photo':
                    await self.application.bot.send_photo(
                        chat_id=channel_id,
                        photo=post['photo'],
                        caption=post.get('caption'),
                        disable_notification=not settings.get('notify', True),
                        protect_content=settings.get('protect', False),
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML if settings.get('format', 'telegram') == 'html' else ParseMode.MARKDOWN_V2
                    )
                elif post['type'] == 'video':
                    await self.application.bot.send_video(
                        chat_id=channel_id,
                        video=post['video'],
                        caption=post.get('caption'),
                        disable_notification=not settings.get('notify', True),
                        protect_content=settings.get('protect', False),
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML if settings.get('format', 'telegram') == 'html' else ParseMode.MARKDOWN_V2
                    )
                elif post['type'] == 'document':
                    await self.application.bot.send_document(
                        chat_id=channel_id,
                        document=post['document'],
                        caption=post.get('caption'),
                        disable_notification=not settings.get('notify', True),
                        protect_content=settings.get('protect', False),
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML if settings.get('format', 'telegram') == 'html' else ParseMode.MARKDOWN_V2
                    )
                elif post['type'] == 'audio':
                    await self.application.bot.send_audio(
                        chat_id=channel_id,
                        audio=post['audio'],
                        caption=post.get('caption'),
                        disable_notification=not settings.get('notify', True),
                        protect_content=settings.get('protect', False),
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML if settings.get('format', 'telegram') == 'html' else ParseMode.MARKDOWN_V2
                    )
                sent += 1
            except Forbidden:
                errors += 1
                failed_channels.append(str(channel_id))
            except Exception:
                errors += 1
                failed_channels.append(str(channel_id))
            # Rate-limit nhẹ
            try:
                await asyncio.sleep(Config.DEFAULT_DELAY_BETWEEN_POSTS)
            except Exception:
                pass
        # Xoá state
        if user_id in self.user_states:
            self.user_states.pop(user_id)
        result_text = f"📤 Đã gửi bài tới {sent}/{len(channels)} kênh."
        if failed_channels:
            failed_list = ", ".join(failed_channels)
            result_text += f"\n⚠️ Không thể gửi tới: {failed_list}.\nHãy kiểm tra xem bot đã được thêm làm admin và có quyền Post Messages chưa."
        await query.edit_message_text(result_text)
    
    async def start_quick_text_post(self, query):
        """Bắt đầu luồng tạo bài đăng text (qua menu Đăng bài nhanh)"""
        user_id = query.from_user.id
        # Lưu trạng thái
        self.user_states[user_id] = {
            'action': 'creating_post',
            'step': 'waiting_content',
            'post_data': {},
            'settings': {} # Khởi tạo settings mới
        }
        await query.edit_message_text(
            "📝 **Tạo bài đăng (Text)**\n\n" \
            "Gửi nội dung bài đăng (chỉ text).",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def start_quick_post(self, query, media_type: str):
        """Bắt đầu luồng tạo bài đăng với loại media chỉ định (photo, video, document)"""
        user_id = query.from_user.id
        # Khởi tạo trạng thái
        prev_state = self.user_states.get(user_id, {})
        settings = prev_state.get('settings', {})
        self.user_states[user_id] = {
            'action': 'creating_post',
            'step': 'waiting_content',
            'post_data': {},
            'expected_media': media_type,  # dùng cho future validation nếu cần
            'settings': settings
        }
        instructions = {
            'photo': "Gửi **1 ảnh** cần đăng.",
            'video': "Gửi **1 video** cần đăng (<= 50 MB).",
            'document': "Gửi **file tài liệu** cần đăng (PDF, ZIP, v.v.)."
        }
        msg = instructions.get(media_type, "Gửi nội dung bài đăng.")
        await query.edit_message_text(
            f"📤 **Tạo bài đăng ({media_type.upper()})**\n\n{msg}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def start_quick_post_any(self, query):
        """Sau khi người dùng bấm Tiếp theo: yêu cầu họ gửi nội dung (text hoặc media bất kỳ)."""
        user_id = query.from_user.id
        # Lấy settings đã cấu hình
        settings = self.user_states.get(user_id, {}).get('settings', {})

        # Khởi tạo trạng thái tạo bài đăng
        self.user_states[user_id] = {
            'action': 'creating_post',
            'step': 'waiting_content',
            'post_data': {},
            'settings': settings
        }

        prompt_text = (
            "✉️ **Gửi nội dung bài đăng**\n\n"
            "Bạn có thể gửi:\n"
            "• Văn bản\n"
            "• Ảnh, Video, Album\n" 
            "• Tệp, Sticker, GIF\n"
            "• Âm thanh, Tin nhắn thoại, Video tròn\n\n"
            "Chỉ cần gửi nội dung vào đây để tiếp tục."
        )

        keyboard = [[
            InlineKeyboardButton("🏠 Menu", callback_data="back_main"),
            InlineKeyboardButton("🔙 Quay lại", callback_data="quick_post")
        ]]
        
        await query.edit_message_text(
            prompt_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cancel_post(self, query):
        """Quay lại menu chính (thay vì hủy)"""
        user_id = query.from_user.id
        if user_id in self.user_states:
            self.user_states.pop(user_id)
        await self.show_admin_panel(query)
    
    async def handle_back_to_previous(self, query):
        """Xử lý quay lại trang trước dựa trên context"""
        user_id = query.from_user.id
        state = self.user_states.get(user_id, {})
        action = state.get('action')
        step = state.get('step')
        
        if action == 'creating_post':
            if step == 'selecting_channels':
                # Từ chọn kênh → quay về thêm nút
                state['step'] = 'adding_buttons'
                await self.show_button_creation_options(query)
            elif step == 'adding_buttons':
                # Từ thêm nút → quay về nhập content 
                state['step'] = 'waiting_content'
                await self.show_content_input_prompt(query)
            else:
                # Mặc định về trang settings
                await self.show_quick_post_intro(query)
        elif action == 'scheduling_post':
            # Từ scheduler về menu chính
            await self.show_admin_panel(query)
        else:
            # Mặc định về menu chính
            await self.show_admin_panel(query)
    
    async def show_button_creation_options(self, query):
        """Hiển thị lại trang tạo nút"""
        user_id = query.from_user.id
        state = self.user_states.get(user_id, {})
        post = state.get('post_data', {})
        
        # Hiển thị hướng dẫn tạo nút
        guide_text = (
            "🎯 **Hướng dẫn tạo nút dưới bài viết**\n\n"
            "**📝 Cú pháp:** `Tên nút | Link`\n\n"
            "**🔗 Các loại nút được hỗ trợ:**\n"
            "• **Nút liên kết thường:**\n"
            "`Tham gia kênh | https://t.me/example`\n\n"
            "• **Nút mở trang web:**\n"
            "`Website | https://example.com`\n\n"
            "• **Nút liên hệ admin:**\n"
            "`Liên hệ | https://t.me/admin`\n\n"
            "• **Nút kênh riêng tư:**\n"
            "`VIP Channel | https://t.me/+NV5LFI4T7n0yZjUx`\n\n"
            "**📋 Tạo nhiều nút:**\n"
            "• **Nhiều nút (mỗi dòng 1 nút):**\n"
            "```\n"
            "Kênh chính | https://t.me/example\n"
            "Website | https://example.com\n"
            "Liên hệ | https://t.me/admin\n"
            "```\n\n"
            "**⚠️ Lưu ý:** Mỗi dòng chỉ được 1 nút, sử dụng dấu `|` để phân tách tên và link"
        )

        keyboard = [
            [InlineKeyboardButton("📚 Nút đã lưu", callback_data="saved_buttons"), InlineKeyboardButton("✏️ Tạo nút thủ công", callback_data="add_buttons_manual")],
            [InlineKeyboardButton("⏭️ Bỏ qua nút", callback_data="skip_add_buttons")],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="back_to_previous")]
        ]
        
        await query.edit_message_text(
            guide_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_content_input_prompt(self, query):
        """Hiển thị lại trang nhập content"""
        await self.start_quick_post_any(query)
    
    async def process_add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
        
        channel_input = update.message.text.strip()
        result = await self.channel_manager.add_channel(channel_input, context.bot)
        
        if result['success']:
            success_text = (
                f"✅ **Đã thêm kênh thành công!**\n\n"
                f"📢 **Tên:** {result['channel_name']}\n"
                f"🆔 **ID:** `{result['channel_id']}`\n"
                f"📋 **Loại:** {result['channel'].get('type', 'channel')}\n"
                f"👤 **Username:** @{result['channel'].get('username', 'Không có')}"
            )
            
            # Reply với thông tin chi tiết
            message = await update.message.reply_text(success_text, parse_mode=ParseMode.MARKDOWN)
            
            # Thông báo cho admin
            await self.notify_admins(f"<b>➕ Đã thêm kênh mới:</b> <code>{result['channel_name']}</code> (ID: {result['channel_id']})")
            
            # Sau 3 giây hiển thị nút quay về manage channels
            keyboard = [[InlineKeyboardButton("📋 Quản lý kênh", callback_data="manage_channels")]]
            await message.edit_text(
                success_text + "\n\n💡 Nhấn nút bên dưới để quay về quản lý kênh.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error_text = f"❌ **Lỗi khi thêm kênh:**\n{result['error']}"
            message = await update.message.reply_text(error_text, parse_mode=ParseMode.MARKDOWN)
            
            # Phân tích lỗi và đưa ra hướng dẫn cụ thể
            error_msg = result['error'].lower()
            
            if 'chat not found' in error_msg or 'not found' in error_msg:
                error_text = (
                    "❌ **Không tìm thấy kênh**\n\n"
                    "🔍 **Nguyên nhân có thể:**\n"
                    "• Username kênh không đúng\n"
                    "• Kênh đã bị xóa hoặc bị khóa\n"
                    "• Link mời đã hết hạn\n\n"
                    "💡 **Giải pháp:**\n"
                    "• Kiểm tra lại @username\n"
                    "• Thử sử dụng link mời mới\n"
                    "• Hoặc sử dụng Chat ID (-100...)"
                )
            elif 'forbidden' in error_msg or 'not enough rights' in error_msg:
                bot_username = (await context.bot.get_me()).username
                error_text = (
                    "🚫 **Bot chưa có quyền truy cập**\n\n"
                    "⚠️ **Cần thực hiện:**\n"
                    f"1. Thêm `@{bot_username}` vào kênh\n"
                    "2. Cấp quyền **Admin** cho bot\n"
                    "3. Bật quyền **'Đăng tin nhắn'**\n"
                    "4. Thử lại\n\n"
                    "📖 Xem hướng dẫn chi tiết ở nút bên dưới."
                )
            else:
                error_text = f"❌ **Lỗi:** {result['error']}\n\n💡 Vui lòng kiểm tra lại thông tin kênh."
            
            message = await update.message.reply_text(error_text, parse_mode=ParseMode.MARKDOWN)
            
            # Hiển thị nút thử lại với hướng dẫn
            bot_username = (await context.bot.get_me()).username
            keyboard = [
                [InlineKeyboardButton("🔄 Thử lại", callback_data="add_channel_prompt")],
                [InlineKeyboardButton("📖 Hướng dẫn", url=f"https://t.me/{bot_username}?start=guide_add_bot")],
                [InlineKeyboardButton("📋 Quản lý kênh", callback_data="manage_channels")]
            ]
            await message.edit_text(
                error_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Clear state
        if user_id in self.user_states:
            self.user_states.pop(user_id)
    
    async def process_channel_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý tìm kiếm kênh"""
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
        
        query_text = update.message.text.strip()
        results = self.channel_manager.search_channels(query_text)
        
        if not results:
            await update.message.reply_text(
                f"🔍 **Không tìm thấy kênh nào với từ khóa:** `{query_text}`\n\n"
                "💡 Thử tìm với:\n"
                "• Tên kênh\n"
                "• Username (có hoặc không có @)\n"
                "• ID kênh",
            parse_mode=ParseMode.MARKDOWN
        )
        else:
            result_text = f"🔍 **Tìm thấy {len(results)} kênh với từ khóa:** `{query_text}`\n\n"
            
            for i, channel in enumerate(results[:10], 1):  # Giới hạn 10 kết quả
                status = "✅" if channel.get('active', True) else "🚫"
                title = channel.get('title', channel.get('name', 'Không có tên'))
                username = f"@{channel.get('username')}" if channel.get('username') else "Không có"
                post_count = channel.get('post_count', 0)
                
                result_text += (
                    f"{i}. {status} **{title}**\n"
                    f"   🆔 ID: `{channel.get('id')}`\n"
                    f"   📢 Username: {username}\n"
                    f"   📊 Bài đăng: {post_count}\n\n"
                )
            
            if len(results) > 10:
                result_text += f"➕ Và {len(results) - 10} kênh khác..."
            
            # Tạo keyboard với các kênh tìm được
            keyboard = []
            for channel in results[:5]:  # Chỉ hiện 5 nút đầu
                ch_id = str(channel.get('id'))
                title = channel.get('title', channel.get('name', ch_id))[:20]
                keyboard.append([
                    InlineKeyboardButton(f"📊 {title}", callback_data=f"channel_stats_{ch_id}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="back_manage_channels")])
            
            await update.message.reply_text(
                result_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Clear state
        if user_id in self.user_states:
            self.user_states.pop(user_id)
    
    async def prompt_add_channel(self, query):
        user_id = query.from_user.id
        self.user_states[user_id] = {
            'action': 'adding_channel',
            'step': 'waiting_channel'
        }
        
        bot_username = (await self.application.bot.get_me()).username
        
        guide_text = (
            "➕ **Thêm kênh mới**\n\n"
            "📋 **Bước 1: Thêm bot vào kênh**\n"
            f"• Vào kênh/nhóm cần thêm\n"
            f"• Nhấn **⚙️ Cài đặt** → **👥 Quản trị viên**\n"
            f"• Nhấn **➕ Thêm quản trị viên**\n"
            f"• Tìm và chọn `@{bot_username}`\n"
            f"• **✅ BẮT BUỘC:** Cấp quyền **'Đăng tin nhắn'**\n\n"
            "📋 **Bước 2: Lấy thông tin kênh**\n"
            "• **Kênh công khai:** Gửi `@username` (ví dụ: @mychannel)\n"
            "• **Kênh riêng tư:** Gửi link mời hoặc ID\n"
            "  - Link: `https://t.me/+ABC123...`\n"
            "  - ID: `-1001234567890`\n\n"
            "⚠️ **Lưu ý quan trọng:**\n"
            "• Bot phải được thêm làm **admin** trước\n"
            "• Bot cần quyền **'Đăng tin nhắn'** để hoạt động\n"
            "• Chỉ admin kênh mới có thể thêm bot\n\n"
            "💡 Gõ `/cancel` để hủy."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📖 Hướng dẫn chi tiết", url=f"https://t.me/{bot_username}?start=guide_add_bot"),
                InlineKeyboardButton("🔄 Quay lại", callback_data="back_manage_channels")
            ]
        ]
        
        await self.safe_edit_message(
            query,
            guide_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def prompt_remove_channel(self, query):
        channels = await self.channel_manager.get_all_channels()
        if not channels:
            await query.edit_message_text(
                "❌ **Chưa có kênh nào để xóa**\n\n💡 Sử dụng nút 'Thêm kênh' để thêm kênh mới.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="back_manage_channels")]]),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        remove_text = (
            f"🗑️ **Xóa kênh** ({len(channels)} kênh)\n\n"
            "⚠️ **Cảnh báo:** Hành động này không thể hoàn tác!\n\n"
            "Chọn kênh cần xóa:"
        )
        
        keyboard = []
        for ch in channels:
            ch_id = str(ch.get('id'))
            title = ch.get('title', ch.get('name', 'Không có tên'))
            status = "✅" if ch.get('active', True) else "🚫"
            post_count = ch.get('post_count', 0)
            
            # Giới hạn độ dài tên hiển thị
            display_name = title[:25] + "..." if len(title) > 25 else title
            button_text = f"🗑️ {status} {display_name} ({post_count} bài)"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"remove_channel_{ch_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="back_manage_channels")])
        
        await query.edit_message_text(
            remove_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def confirm_remove_channel(self, query, data: str):
        channel_id = data.replace("remove_channel_", "")
        
        # Lấy thông tin kênh trước khi xóa để hiển thị
        channel = await self.channel_manager.get_channel(channel_id)
        channel_name = channel.get('title', channel_id) if channel else channel_id
        
        removed = await self.channel_manager.remove_channel(channel_id)
        
        if removed:
            await query.answer(f"✅ Đã xóa kênh {channel_name}")
            # Thông báo cho admin
            await self.notify_admins(f"<b>🗑️ Đã xoá kênh:</b> <code>{channel_name}</code> (ID: {channel_id})")
        else:
            await query.answer("❌ Không tìm thấy kênh hoặc lỗi khi xóa.", show_alert=True)
        
        # Quay về trang quản lý kênh
        await self.show_manage_channels(query)



    async def notify_admins(self, text: str):
        """Gửi thông báo realtime tới tất cả admin."""
        for admin_id in Config.ADMIN_IDS:
            try:
                await self.application.bot.send_message(chat_id=admin_id, text=text, parse_mode=ParseMode.HTML)
            except Exception:
                pass
    
    def run(self):
        """Chạy bot"""
        print("🤖 Bot đăng bài đang khởi động...")
        print("📱 Nhấn Ctrl+C để dừng bot")

        # Đảm bảo có event loop
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        try:
            # Bắt đầu scheduler
            self.scheduler.start()
            
            # Chạy bot
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except KeyboardInterrupt:
            print("\n🛑 Bot đã dừng!")
        finally:
            # Dừng scheduler
            self.scheduler.stop()

    async def process_schedule_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lưu nội dung rồi hỏi thời gian"""
        # Tái sử dụng process_post_content logic nhưng internal
        await self.process_post_content(update, context)
        # Sau khi nhận nội dung -> bước chọn kênh (đã hiển thị keyboard trong process_post_content)
        user_id = update.effective_user.id if update.effective_user else 0
        if user_id in self.user_states:
            self.user_states[user_id]['action'] = 'scheduling_post'
            # step đã là selecting_channels

    async def process_schedule_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận thời gian, tạo lịch"""
        input_text = update.message.text.strip()
        user_id = update.effective_user.id if update.effective_user else 0
        state = self.user_states.get(user_id, {})
        try:
            day_part = datetime.strptime(input_text, "%H:%M %d/%m/%Y")
            if day_part < datetime.now():
                raise ValueError("Time in past")
        except Exception:
            await update.message.reply_text("❌ Định dạng sai! Hãy nhập HH:MM DD/MM/YYYY và là thời gian tương lai.")
            return
        post_data: Dict[str, Any] = state.get('post_data', {})
        if not post_data:
            await update.message.reply_text("❌ Chưa có nội dung bài đăng!")
            return
        channels = await self.channel_manager.get_all_channels()
        schedule_id = await self.scheduler.schedule_post(post_data, channels, day_part)
        if user_id in self.user_states:
            self.user_states.pop(user_id)
        await update.message.reply_text(
            f"✅ Đã lên lịch <code>{schedule_id}</code> vào {day_part.strftime('%H:%M %d/%m/%Y')}",
            parse_mode=ParseMode.HTML
        )

    async def list_schedules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Liệt kê lịch đăng"""
        if not update.message:
            return
        user_id = self.check_user_and_admin(update)
        if user_id is None or not await self.is_admin(user_id):
            return
        schedules = await self.scheduler.get_scheduled_posts("pending")
        if not schedules:
            await update.message.reply_text("⏰ Không có lịch nào đang chờ.")
            return
        keyboard = []
        for s in schedules[:10]:
            label = datetime.fromisoformat(s['next_execution']).strftime('%H:%M %d/%m')
            keyboard.append([InlineKeyboardButton(f"❌ {label}", callback_data=f"cancel_schedule_{s['id']}")])
        keyboard.append([InlineKeyboardButton("🗑️ Huỷ tất cả", callback_data="cancel_all_schedules")])
        await update.message.reply_text("⏰ **Lịch đang chờ:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def handle_cancel_schedule(self, query, data: str):
        sched_id = data.replace("cancel_schedule_", "")
        ok = await self.scheduler.cancel_schedule(sched_id)
        await query.answer()
        await query.edit_message_text("✅ Đã huỷ lịch" if ok else "❌ Không tìm thấy lịch.")

    async def handle_cancel_all_schedules(self, query):
        schedules = await self.scheduler.get_scheduled_posts("pending")
        for s in schedules:
            await self.scheduler.cancel_schedule(s['id'])
        await query.answer()
        await query.edit_message_text("🗑️ Đã huỷ tất cả lịch đang chờ!")

    async def cancel_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Huỷ luồng thao tác hiện tại"""
        if not update.message:
            return
        user_id = self.check_user_and_admin(update)
        if user_id in self.user_states:
            self.user_states.pop(user_id)
        await update.message.reply_text("✅ Đã huỷ thao tác hiện tại.")

    # ---------- Buttons flow ----------
    async def show_button_help(self, query):
        """Hiển thị hướng dẫn định dạng nút (giống screenshot)."""
        help_text = (
            "**Cách thêm nút vào bài đăng**\n\n"
            "Định dạng mỗi dòng: \`Tên nút | https://link\`\n\n"
            "Ví dụ:\n"
            "• Nút đơn: `Theo dõi kênh | https://t.me/example`\n"
            "• Nhiều nút trong 1 hàng: `Web | https://example.com && Fanpage | https://facebook.com`\n"
            "• Nhiều hàng nút: gửi nhiều dòng mỗi dòng 1 hoặc nhiều nút."
        )
        await query.answer()
        await query.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def prompt_manual_buttons(self, query):
        """Yêu cầu người dùng nhập thủ công danh sách nút"""
        await query.answer()
        
        guide_text = (
            "✏️ **Tạo nút thủ công**\n\n"
            "**Cú pháp:** `Tên nút | Link`\n\n"
            "**Ví dụ:**\n"
            "```\n"
            "Tham gia kênh | https://t.me/example\n"
            "Website | https://website.com\n"
            "Liên hệ | https://t.me/admin\n"
            "```\n\n"
            "📝 Gửi từng dòng một nút, hoặc nhiều dòng cho nhiều nút.\n"
            "💡 Gõ 'xong' hoặc 'bỏ qua' để hoàn tất."
        )
        
        keyboard = [[
            InlineKeyboardButton("🔙 Quay lại", callback_data="back_to_previous"),
            InlineKeyboardButton("⏭️ Bỏ qua nút", callback_data="skip_add_buttons")
        ]]
        
        await query.edit_message_text(
            guide_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_skip_add_buttons(self, query):
        """Người dùng bỏ qua bước thêm nút"""
        await query.answer()
        user_id = query.from_user.id
        state = self.user_states.get(user_id)
        if state:
            state['step'] = 'selecting_channels'
            await self.show_channel_selection(query, None)

    async def show_saved_buttons(self, query):
        """Hiển thị danh sách các bộ nút đã lưu để chọn nhanh"""
        await query.answer()
        if not self.saved_buttons:
            await query.message.reply_text("📚 Chưa có bộ nút nào được lưu.")
            return

        keyboard = []
        for idx, btns in enumerate(self.saved_buttons):
            label = btns[0].get('text', f'Set {idx+1}')[:20]
            keyboard.append([InlineKeyboardButton(label, callback_data=f"use_saved_btn_{idx}")])
        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")])

        await query.message.reply_text("📚 **Chọn bộ nút đã lưu:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def handle_webapp_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận data JSON từ mini-app và chuyển thành buttons."""
        if not update.message or not update.message.web_app_data:
            return
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
        state = self.user_states.get(user_id)
        if not state or state.get('action') != 'creating_post':
            # Nếu không trong trạng thái tạo post, thông báo
            await update.message.reply_text("❌ Hãy bắt đầu tạo bài đăng trước khi sử dụng mini-app.")
            return

        try:
            # Parse dữ liệu từ mini-app
            raw_data = update.message.web_app_data.data
            print(f"Received WebApp data: {raw_data}")  # Debug log
            
            items = json.loads(raw_data)
            
            # items là list dict {text, url} từ mini-app mới
            buttons = []
            for it in items:
                # Mini-app gửi {text, url}, đã đúng format
                text = it.get('text', '').strip()
                url = it.get('url', '').strip()
                if text and url:
                    buttons.append({'text': text, 'url': url})
            
            if buttons:
                state.setdefault('post_data', {})['buttons'] = buttons
                self._add_saved_buttons(buttons)
                
                # Thông báo thành công
                await update.message.reply_text(
                    f"✅ Đã thêm {len(buttons)} nút từ mini-app!\n"
                    "Bạn có thể xem preview bên dưới.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
            else:
                await update.message.reply_text("❌ Không có nút hợp lệ nào được nhận.")
                return
                
        except Exception as e:
            print(f"Error parsing WebApp data: {e}")  # Debug log
            await update.message.reply_text(f"❌ Lỗi parse buttons: {e}")
            return

        # Hiển thị preview bài đăng với nút và chuyển sang chọn kênh
        post = state.get('post_data', {})
        reply_markup = None
        if post.get('buttons'):
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(btn['text'], url=btn['url'])] for btn in post['buttons']])

        try:
            if post.get('type') == 'text':
                await update.message.reply_text(post.get('text', ''), reply_markup=reply_markup, disable_web_page_preview=True)
            elif post.get('type') == 'photo':
                await update.message.reply_photo(post.get('photo'), caption=post.get('caption'), reply_markup=reply_markup)
            elif post.get('type') == 'video':
                await update.message.reply_video(post.get('video'), caption=post.get('caption'), reply_markup=reply_markup)
            elif post.get('type') == 'document':
                await update.message.reply_document(post.get('document'), caption=post.get('caption'), reply_markup=reply_markup)
            elif post.get('type') == 'audio':
                await update.message.reply_audio(post.get('audio'), caption=post.get('caption'), reply_markup=reply_markup)
        except Exception:
            pass

        # Chuyển sang bước chọn kênh
        state['step'] = 'selecting_channels'
        await self.show_channel_selection(update.message, context)

    async def debug_all_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Debug handler để log tất cả message"""
        if update.message:
            print(f"DEBUG: Received message type: {update.message.content_type}")
            if hasattr(update.message, 'web_app_data') and update.message.web_app_data:
                print(f"DEBUG: WebApp data detected: {update.message.web_app_data.data}")
            if update.message.text:
                print(f"DEBUG: Text message: {update.message.text[:50]}...")

    # ---------- Saved buttons helpers ----------

    def _load_saved_buttons(self) -> List[List[Dict[str, str]]]:
        try:
            if self._saved_buttons_file.exists():
                with open(self._saved_buttons_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_saved_buttons(self):
        try:
            with open(self._saved_buttons_file, 'w', encoding='utf-8') as f:
                json.dump(self.saved_buttons, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _add_saved_buttons(self, buttons: List[Dict[str, str]]):
        if not buttons:
            return
        # Avoid exact duplicate
        if buttons in self.saved_buttons:
            return
        self.saved_buttons.insert(0, buttons)
        # Limit to 10
        self.saved_buttons = self.saved_buttons[:10]
        self._save_saved_buttons()

    async def show_channel_stats(self, query, channel_id: str):
        """Hiển thị thống kê chi tiết của kênh"""
        channel = await self.channel_manager.get_channel(channel_id)
        if not channel:
            await query.answer("❌ Không tìm thấy kênh!", show_alert=True)
            return
        
        # Tính toán thống kê
        total_posts = channel.get('post_count', 0)
        success_posts = channel.get('success_count', 0)
        failed_posts = channel.get('fail_count', 0)
        success_rate = (success_posts / total_posts * 100) if total_posts > 0 else 0
        
        # Thời gian
        added_date = channel.get('added_date', 'Không rõ')
        last_post = channel.get('last_post', 'Chưa có')
        
        # Format dates
        if added_date != 'Không rõ':
            try:
                from datetime import datetime
                added_dt = datetime.fromisoformat(added_date.replace('Z', '+00:00'))
                added_date = added_dt.strftime('%d/%m/%Y %H:%M')
            except:
                pass
                
        if last_post != 'Chưa có':
            try:
                last_dt = datetime.fromisoformat(last_post.replace('Z', '+00:00'))
                last_post = last_dt.strftime('%d/%m/%Y %H:%M')
            except:
                pass
        
        stats_text = (
            f"📊 **Thống kê kênh: {channel.get('title', channel_id)}**\n\n"
            f"🆔 **ID:** `{channel.get('id')}`\n"
            f"📢 **Username:** @{channel.get('username', 'Không có')}\n"
            f"📋 **Loại:** {channel.get('type', 'channel')}\n"
            f"🔄 **Trạng thái:** {'✅ Hoạt động' if channel.get('active', True) else '🚫 Tắt'}\n\n"
            
            f"📈 **Thống kê đăng bài:**\n"
            f"• Tổng bài đăng: {total_posts}\n"
            f"• Thành công: {success_posts}\n"
            f"• Thất bại: {failed_posts}\n"
            f"• Tỷ lệ thành công: {success_rate:.1f}%\n\n"
            
            f"🕒 **Thời gian:**\n"
            f"• Ngày thêm: {added_date}\n"
            f"• Lần đăng cuối: {last_post}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔑 Kiểm tra quyền", callback_data=f"channel_permissions_{channel_id}"),
                InlineKeyboardButton("🔄 Làm mới", callback_data=f"channel_stats_{channel_id}")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="back_manage_channels")]
        ]
        
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def check_channel_permissions_ui(self, query, channel_id: str):
        """Kiểm tra quyền bot trong kênh"""
        await query.answer("🔍 Đang kiểm tra quyền...", show_alert=False)
        
        permissions = await self.channel_manager.check_channel_permissions(channel_id, self.application.bot)
        
        if 'error' in permissions:
            perm_text = (
                f"❌ **Lỗi kiểm tra quyền kênh {channel_id}**\n\n"
                f"🚫 **Lỗi:** {permissions['error']}\n\n"
                "💡 **Có thể do:**\n"
                "• Bot không có quyền truy cập kênh\n"
                "• Kênh đã bị xóa hoặc thay đổi ID\n"
                "• Bot bị chặn trong kênh"
            )
        else:
            status_icon = "✅" if permissions['is_admin'] else "❌"
            post_icon = "✅" if permissions.get('can_post', False) else "❌"
            edit_icon = "✅" if permissions.get('can_edit', False) else "❌"
            delete_icon = "✅" if permissions.get('can_delete', False) else "❌"
            
            perm_text = (
                f"🔑 **Quyền bot trong kênh {channel_id}**\n\n"
                f"👤 **Vai trò:** {permissions.get('status', 'Unknown')}\n"
                f"{status_icon} **Admin:** {'Có' if permissions['is_admin'] else 'Không'}\n\n"
                
                f"📝 **Quyền cụ thể:**\n"
                f"{post_icon} Đăng bài: {'Có' if permissions.get('can_post', False) else 'Không'}\n"
                f"{edit_icon} Sửa tin nhắn: {'Có' if permissions.get('can_edit', False) else 'Không'}\n"
                f"{delete_icon} Xóa tin nhắn: {'Có' if permissions.get('can_delete', False) else 'Không'}\n\n"
            )
            
            if not permissions['is_admin']:
                perm_text += "⚠️ **Cảnh báo:** Bot không có quyền admin, có thể không đăng bài được!"
            elif not permissions.get('can_post', False):
                perm_text += "⚠️ **Cảnh báo:** Bot không có quyền đăng bài!"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Kiểm tra lại", callback_data=f"channel_permissions_{channel_id}"),
                InlineKeyboardButton("📊 Thống kê", callback_data=f"channel_stats_{channel_id}")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="back_manage_channels")]
        ]
        
        await query.edit_message_text(
            perm_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_channel_search(self, query):
        """Hiển thị tìm kiếm kênh"""
        user_id = query.from_user.id
        self.user_states[user_id] = {
            'action': 'searching_channel',
            'step': 'waiting_query'
        }
        
        search_text = (
            "🔍 **Tìm kiếm kênh**\n\n"
            "Gửi từ khóa để tìm kiếm theo:\n"
            "• Tên kênh\n"
            "• Username (@channel)\n"
            "• ID kênh\n\n"
            "💡 Gõ /cancel để hủy"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data="back_manage_channels")]]
        
        await query.edit_message_text(
            search_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_bulk_channel_actions(self, query):
        """Hiển thị hành động hàng loạt cho kênh"""
        all_channels = await self.channel_manager.get_all_channels()
        active_count = len([c for c in all_channels if c.get('active', True)])
        inactive_count = len(all_channels) - active_count
        
        bulk_text = (
            f"⚡ **Hành động hàng loạt** ({len(all_channels)} kênh)\n\n"
            f"✅ Đang hoạt động: {active_count}\n"
            f"🚫 Đang tắt: {inactive_count}\n\n"
            "Chọn hành động áp dụng cho tất cả kênh:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Bật tất cả", callback_data="toggle_all_channels_on"),
                InlineKeyboardButton("🚫 Tắt tất cả", callback_data="toggle_all_channels_off")
            ],
            [
                InlineKeyboardButton("🗑️ Xóa kênh không hoạt động", callback_data="cleanup_inactive_channels"),
                InlineKeyboardButton("📊 Xuất thống kê", callback_data="export_channel_stats")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="back_manage_channels")]
        ]
        
        await query.edit_message_text(
            bulk_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_channel_backup_options(self, query):
        """Hiển thị tùy chọn sao lưu kênh"""
        backup_text = (
            "💾 **Sao lưu & Khôi phục kênh**\n\n"
            "Chọn hành động:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📤 Xuất danh sách", callback_data="export_channels"),
                InlineKeyboardButton("📥 Nhập danh sách", callback_data="import_channels")
            ],
            [
                InlineKeyboardButton("💾 Sao lưu tự động", callback_data="auto_backup_settings"),
                InlineKeyboardButton("🔄 Khôi phục", callback_data="restore_channels")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="back_manage_channels")]
        ]
        
        await query.edit_message_text(
            backup_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_bulk_toggle(self, query, enable: bool):
        """Xử lý bật/tắt tất cả kênh"""
        action_text = "bật" if enable else "tắt"
        await query.answer(f"🔄 Đang {action_text} tất cả kênh...", show_alert=False)
        
        all_channels = await self.channel_manager.get_all_channels()
        updated_count = 0
        
        for channel in all_channels:
            channel_id = str(channel.get('id'))
            current_status = channel.get('active', True)
            
            if current_status != enable:
                await self.channel_manager.toggle_channel_status(channel_id)
                updated_count += 1
        
        result_text = f"✅ Đã {action_text} {updated_count} kênh!"
        await query.answer(result_text, show_alert=True)
        
        # Refresh the manage channels page
        await self.show_manage_channels(query)

    async def handle_cleanup_inactive(self, query):
        """Xử lý hành động xóa kênh không hoạt động"""
        await query.answer("🗑️ Đang xử lý xóa kênh không hoạt động...")
        all_channels = await self.channel_manager.get_all_channels()
        inactive_channels = [ch for ch in all_channels if not ch.get('active', True)]
        if not inactive_channels:
            await query.edit_message_text("❌ Không có kênh nào không hoạt động để xóa.")
            return
        confirm_text = f"🗑️ Bạn có chắc chắn muốn xóa {len(inactive_channels)} kênh không hoạt động này không? 🚨"
        keyboard = [
            [InlineKeyboardButton("✅ Đồng ý", callback_data="confirm_cleanup_inactive")],
            [InlineKeyboardButton("🚫 Hủy", callback_data="back_manage_channels")]
        ]
        await query.edit_message_text(confirm_text, reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_export_stats(self, query):
        """Xử lý hành động xuất thống kê kênh"""
        await query.answer("📊 Đang xử lý xuất thống kê kênh...")
        all_channels = await self.channel_manager.get_all_channels()
        stats_text = "📊 **Thống kê kênh:**\n\n"
        for ch in all_channels:
            stats_text += f"🆔 **ID:** `{ch.get('id')}`\n"
            stats_text += f"📢 **Username:** @{ch.get('username', 'Không có')}\n"
            stats_text += f"📋 **Loại:** {ch.get('type', 'channel')}\n"
            stats_text += f"🔄 **Trạng thái:** {'✅ Hoạt động' if ch.get('active', True) else '🚫 Tắt'}\n\n"
            stats_text += f"📈 **Thống kê đăng bài:**\n"
            stats_text += f"• Tổng bài đăng: {ch.get('post_count', 0)}\n"
            stats_text += f"• Thành công: {ch.get('success_count', 0)}\n"
            stats_text += f"• Thất bại: {ch.get('fail_count', 0)}\n"
            stats_text += f"• Tỷ lệ thành công: {ch.get('success_rate', 0)}%\n\n"
            stats_text += f"🕒 **Thời gian:**\n"
            stats_text += f"• Ngày thêm: {ch.get('added_date', 'Không rõ')}\n"
            stats_text += f"• Lần đăng cuối: {ch.get('last_post', 'Chưa có')}\n\n"
        await query.edit_message_text(stats_text, parse_mode=ParseMode.MARKDOWN)

    async def handle_export_channels(self, query):
        """Xử lý hành động xuất danh sách kênh"""
        await query.answer("📤 Đang xử lý xuất danh sách kênh...")
        all_channels = await self.channel_manager.get_all_channels()
        channels_text = "📤 **Danh sách kênh:**\n\n"
        for ch in all_channels:
            channels_text += f"🆔 **ID:** `{ch.get('id')}`\n"
            channels_text += f"📢 **Username:** @{ch.get('username', 'Không có')}\n"
            channels_text += f"📋 **Loại:** {ch.get('type', 'channel')}\n"
            channels_text += f"🔄 **Trạng thái:** {'✅ Hoạt động' if ch.get('active', True) else '🚫 Tắt'}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Quay lại", callback_data="channel_backup")]
        ]
        await query.edit_message_text(
            channels_text, 
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_import_channels(self, query):
        """Xử lý hành động nhập danh sách kênh"""
        await query.answer("📥 Đang xử lý nhập danh sách kênh...")
        
        import_text = (
            "📥 **Nhập danh sách kênh**\n\n"
            "Vui lòng gửi danh sách kênh theo định dạng sau:\n\n"
            "🆔 **ID kênh**\n"
            "📢 **Username**\n"
            "📋 **Loại**\n"
            "🔄 **Trạng thái**\n\n"
            "**Ví dụ:**\n"
            "🆔 123456789\n"
            "📢 @example\n"
            "📋 channel\n"
            "🔄 ✅\n\n"
            "💡 **Lưu ý:** Chỉ nhập các kênh đã được đồng bộ hóa với bot."
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Quay lại", callback_data="channel_backup")]
        ]
        await query.edit_message_text(
            import_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    # ---------- Utility methods ----------

    async def safe_edit_message(self, query, text: str, reply_markup=None, parse_mode=None):
        """Safely edit message with exception handling for 'message not modified' error"""
        try:
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e:
            if "message is not modified" in str(e).lower():
                # Message content hasn't changed, just answer the callback
                await query.answer()
            else:
                # Re-raise other exceptions
                raise e

    # ---------- Post History Management ----------
    
    async def show_post_detailed_stats(self, query):
        """Hiển thị thống kê chi tiết lịch sử đăng bài"""
        stats = await self.post_manager.get_statistics()
        all_posts = await self.post_manager.get_post_history(limit=100)
        
        # Thống kê theo loại bài đăng
        type_stats = {}
        for post in all_posts:
            post_type = post.get('type', 'text')
            type_stats[post_type] = type_stats.get(post_type, 0) + 1
        
        # Thống kê theo ngày (7 ngày gần nhất)
        daily_stats = {}
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).date()
            daily_stats[date] = 0
        
        for post in all_posts:
            try:
                post_date = datetime.fromisoformat(post.get('created_at', '')).date()
                if post_date in daily_stats:
                    daily_stats[post_date] += 1
            except:
                pass
        
        stats_text = (
            f"📊 **Thống kê chi tiết lịch sử đăng bài**\n\n"
            f"📈 **Tổng quan:**\n"
            f"• Tổng bài đăng: {stats['total_posts']}\n"
            f"• Thành công: {stats['successful_posts']} ({stats['success_rate']:.1f}%)\n"
            f"• Thất bại: {stats['failed_posts']}\n"
            f"• Hôm nay: {stats['today_posts']} bài (Thành công: {stats['today_success']})\n"
            f"• Kênh phổ biến: {stats['top_channel']}\n\n"
            
            f"📝 **Theo loại bài đăng:**\n"
        )
        
        type_icons = {'text': '📝', 'photo': '🖼️', 'video': '🎥', 'document': '📄', 'audio': '🎵'}
        for post_type, count in type_stats.items():
            icon = type_icons.get(post_type, '📄')
            percentage = (count / len(all_posts) * 100) if all_posts else 0
            stats_text += f"• {icon} {post_type.title()}: {count} ({percentage:.1f}%)\n"
        
        stats_text += f"\n📅 **7 ngày gần nhất:**\n"
        for date in sorted(daily_stats.keys(), reverse=True):
            count = daily_stats[date]
            date_str = date.strftime('%d/%m')
            stats_text += f"• {date_str}: {count} bài\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📤 Xuất báo cáo", callback_data="history_export"),
                InlineKeyboardButton("🔄 Làm mới", callback_data="history_detailed_stats")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="post_history")]
        ]
        
        await self.safe_edit_message(
            query,
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_post_history_filters(self, query):
        """Hiển thị bộ lọc lịch sử đăng bài"""
        filter_text = (
            "🔍 **Bộ lọc lịch sử đăng bài**\n\n"
            "Chọn tiêu chí lọc:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📅 Theo ngày", callback_data="filter_by_date"),
                InlineKeyboardButton("📝 Theo loại", callback_data="filter_by_type")
            ],
            [
                InlineKeyboardButton("✅ Chỉ thành công", callback_data="filter_success_only"),
                InlineKeyboardButton("❌ Chỉ thất bại", callback_data="filter_failed_only")
            ],
            [
                InlineKeyboardButton("📢 Theo kênh", callback_data="filter_by_channel"),
                InlineKeyboardButton("🗂️ Xóa bộ lọc", callback_data="filter_clear")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="post_history")]
        ]
        
        await self.safe_edit_message(
            query,
            filter_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_post_cleanup_options(self, query):
        """Hiển thị tùy chọn dọn dẹp lịch sử đăng bài"""
        all_posts = await self.post_manager.get_post_history(limit=1000)
        
        # Tính toán số bài đăng cũ
        cutoff_30 = datetime.now() - timedelta(days=30)
        cutoff_90 = datetime.now() - timedelta(days=90)
        
        old_30_count = 0
        old_90_count = 0
        
        for post in all_posts:
            try:
                post_date = datetime.fromisoformat(post.get('created_at', ''))
                if post_date < cutoff_90:
                    old_90_count += 1
                elif post_date < cutoff_30:
                    old_30_count += 1
            except:
                pass
        
        cleanup_text = (
            f"🗑️ **Dọn dẹp lịch sử đăng bài**\n\n"
            f"📊 **Thống kê:**\n"
            f"• Tổng bài đăng: {len(all_posts)}\n"
            f"• Cũ hơn 30 ngày: {old_30_count} bài\n"
            f"• Cũ hơn 90 ngày: {old_90_count} bài\n\n"
            f"⚠️ **Cảnh báo:** Hành động không thể hoàn tác!\n\n"
            f"Chọn hành động:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(f"🗑️ Xóa cũ 30 ngày ({old_30_count})", callback_data="cleanup_posts_30"),
                InlineKeyboardButton(f"🗑️ Xóa cũ 90 ngày ({old_90_count})", callback_data="cleanup_posts_90")
            ],
            [
                InlineKeyboardButton("🗑️ Xóa chỉ bài thất bại", callback_data="cleanup_failed_only"),
                InlineKeyboardButton("🗑️ Xóa tất cả", callback_data="cleanup_all_posts")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="post_history")]
        ]
        
        await self.safe_edit_message(
            query,
            cleanup_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_post_history_export(self, query):
        """Xuất dữ liệu lịch sử đăng bài"""
        await query.answer("📤 Đang xuất dữ liệu...", show_alert=False)
        
        try:
            # Xuất dữ liệu thống kê
            stats = await self.post_manager.get_statistics()
            all_posts = await self.post_manager.get_post_history(limit=1000)
            
            export_text = (
                f"📤 **Báo cáo lịch sử đăng bài**\n"
                f"📅 Xuất lúc: {datetime.now().strftime('%H:%M %d/%m/%Y')}\n\n"
                
                f"📊 **Thống kê tổng quan:**\n"
                f"• Tổng bài đăng: {stats['total_posts']}\n"
                f"• Thành công: {stats['successful_posts']} ({stats['success_rate']:.1f}%)\n"
                f"• Thất bại: {stats['failed_posts']}\n"
                f"• Hôm nay: {stats['today_posts']} bài\n"
                f"• Kênh phổ biến: {stats['top_channel']}\n\n"
                
                f"📋 **Chi tiết {min(len(all_posts), 20)} bài gần nhất:**\n"
            )
            
            for i, post in enumerate(all_posts[:20], 1):
                post_id = post.get('id', 'Unknown')
                post_type = post.get('type', 'text')
                created_at = post.get('created_at', '')
                
                try:
                    dt = datetime.fromisoformat(created_at)
                    time_str = dt.strftime('%H:%M %d/%m/%Y')
                except:
                    time_str = 'N/A'
                
                channels_data = post.get('channels', {})
                success_channels = sum(1 for ch in channels_data.values() if ch.get('success', False))
                total_channels = len(channels_data)
                
                export_text += f"`{i}.` {post_id} ({post_type}) - {time_str} - {success_channels}/{total_channels} kênh\n"
            
            if len(all_posts) > 20:
                export_text += f"\n... và {len(all_posts) - 20} bài khác"
            
            keyboard = [
                [InlineKeyboardButton("💾 Lưu file JSON", callback_data="export_posts_json")],
                [InlineKeyboardButton("🔙 Quay lại", callback_data="post_history")]
            ]
            
            await self.safe_edit_message(
                query,
                export_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await query.answer(f"❌ Lỗi xuất dữ liệu: {str(e)}", show_alert=True)
    
    # ---------- Utility methods ----------

    # ---------- Settings Management ----------
    
    async def handle_settings_callback(self, query, data: str):
        """Xử lý callback cho cài đặt"""
        action = data.replace("settings_", "")
        
        if action == "bot":
            await self.show_bot_settings(query)
        elif action == "scheduler":
            await self.show_scheduler_settings(query)
        elif action == "notifications":
            await self.show_notification_settings(query)
        elif action == "backup":
            await self.show_backup_settings(query)
        elif action == "security":
            await self.show_security_settings(query)
        elif action == "interface":
            await self.show_interface_settings(query)
        elif action == "advanced":
            await self.show_advanced_settings(query)
        elif action == "export":
            await self.show_export_import_settings(query)
        elif action == "reset_all":
            await self.confirm_reset_all_settings(query)
        elif action == "validate":
            await self.validate_all_settings(query)
        elif action.startswith("toggle_"):
            await self.toggle_setting(query, action)
        elif action.startswith("set_"):
            await self.handle_set_setting(query, action)
        elif action.startswith("enable_all_notif") or action.startswith("disable_all_notif"):
            await self.handle_bulk_notification_toggle(query, action)
        elif action.startswith("backup_now") or action.startswith("export_now") or action.startswith("confirm_reset"):
            await self.handle_settings_action(query, action)
        else:
            await query.answer("🚧 Cài đặt này đang phát triển!", show_alert=False)
    
    async def show_bot_settings(self, query):
        """Hiển thị cài đặt bot"""
        bot_settings = self.settings_manager.get_category("bot")
        
        def bool_icon(val: bool) -> str:
            return "✅" if val else "❌"
        
        settings_text = (
            f"🤖 **Cài đặt Bot**\n\n"
            f"⏱️ **Delay giữa bài đăng:** {bot_settings.get('delay_between_posts', 2)} giây\n"
            f"📊 **Tối đa kênh/lần:** {bot_settings.get('max_channels_per_post', 50)}\n"
            f"📝 **Parse mode mặc định:** {bot_settings.get('default_parse_mode', 'Markdown')}\n"
            f"🔗 **Tắt preview link:** {bool_icon(bot_settings.get('disable_web_page_preview', False))}\n"
            f"🔔 **Thông báo mặc định:** {bool_icon(bot_settings.get('default_notification', True))}\n"
            f"🔒 **Bảo vệ nội dung:** {bool_icon(bot_settings.get('default_protect_content', False))}\n"
            f"⚡ **Rate limit:** {bool_icon(bot_settings.get('rate_limit_enabled', True))} ({bot_settings.get('rate_limit_per_minute', 20)}/phút)\n\n"
            f"⚙️ **Chọn cài đặt để thay đổi:**"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("⏱️ Delay", callback_data="settings_set_delay"),
                InlineKeyboardButton("📊 Max kênh", callback_data="settings_set_max_channels")
            ],
            [
                InlineKeyboardButton("📝 Parse mode", callback_data="settings_toggle_parse_mode"),
                InlineKeyboardButton("🔗 Preview", callback_data="settings_toggle_preview")
            ],
            [
                InlineKeyboardButton("🔔 Thông báo", callback_data="settings_toggle_notification"),
                InlineKeyboardButton("🔒 Bảo vệ", callback_data="settings_toggle_protect")
            ],
            [
                InlineKeyboardButton("⚡ Rate limit", callback_data="settings_toggle_rate_limit"),
                InlineKeyboardButton("🔄 Reset mặc định", callback_data="settings_reset_bot")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="settings")]
        ]
        
        await self.safe_edit_message(
            query,
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_scheduler_settings(self, query):
        """Hiển thị cài đặt scheduler"""
        scheduler_settings = self.settings_manager.get_category("scheduler")
        
        def bool_icon(val: bool) -> str:
            return "✅" if val else "❌"
        
        settings_text = (
            f"⏰ **Cài đặt Lịch đăng**\n\n"
            f"🔄 **Interval kiểm tra:** {scheduler_settings.get('check_interval', 30)} giây\n"
            f"🗑️ **Tự động xóa sau:** {scheduler_settings.get('auto_cleanup_days', 30)} ngày\n"
            f"📊 **Tối đa lịch đăng:** {scheduler_settings.get('max_scheduled_posts', 100)} bài\n"
            f"🔁 **Cho phép lặp lại:** {bool_icon(scheduler_settings.get('enable_repeat_posts', True))}\n"
            f"🌍 **Timezone:** {scheduler_settings.get('default_timezone', 'Asia/Ho_Chi_Minh')}\n\n"
            f"⚙️ **Chọn cài đặt để thay đổi:**"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Interval", callback_data="settings_set_scheduler_interval"),
                InlineKeyboardButton("🗑️ Cleanup", callback_data="settings_set_cleanup_days")
            ],
            [
                InlineKeyboardButton("📊 Max lịch", callback_data="settings_set_max_schedules"),
                InlineKeyboardButton("🔁 Lặp lại", callback_data="settings_toggle_repeat")
            ],
            [
                InlineKeyboardButton("🌍 Timezone", callback_data="settings_set_timezone"),
                InlineKeyboardButton("🔄 Reset", callback_data="settings_reset_scheduler")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="settings")]
        ]
        
        await self.safe_edit_message(
            query,
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_notification_settings(self, query):
        """Hiển thị cài đặt thông báo"""
        notification_settings = self.settings_manager.get_category("notifications")
        
        def bool_icon(val: bool) -> str:
            return "✅" if val else "❌"
        
        settings_text = (
            f"🔔 **Cài đặt Thông báo**\n\n"
            f"👤 **Thông báo admin:** {bool_icon(notification_settings.get('admin_notifications', True))}\n"
            f"✅ **Đăng bài thành công:** {bool_icon(notification_settings.get('post_success_notifications', True))}\n"
            f"❌ **Đăng bài thất bại:** {bool_icon(notification_settings.get('post_failure_notifications', True))}\n"
            f"📊 **Trạng thái kênh:** {bool_icon(notification_settings.get('channel_status_notifications', True))}\n"
            f"⏰ **Lịch đăng bài:** {bool_icon(notification_settings.get('scheduler_notifications', True))}\n"
            f"🚨 **Thông báo lỗi:** {bool_icon(notification_settings.get('error_notifications', True))}\n\n"
            f"⚙️ **Chọn để bật/tắt:**"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("👤 Admin", callback_data="settings_toggle_admin_notif"),
                InlineKeyboardButton("✅ Thành công", callback_data="settings_toggle_success_notif")
            ],
            [
                InlineKeyboardButton("❌ Thất bại", callback_data="settings_toggle_failure_notif"),
                InlineKeyboardButton("📊 Kênh", callback_data="settings_toggle_channel_notif")
            ],
            [
                InlineKeyboardButton("⏰ Scheduler", callback_data="settings_toggle_scheduler_notif"),
                InlineKeyboardButton("🚨 Lỗi", callback_data="settings_toggle_error_notif")
            ],
            [
                InlineKeyboardButton("✅ Bật tất cả", callback_data="settings_enable_all_notif"),
                InlineKeyboardButton("❌ Tắt tất cả", callback_data="settings_disable_all_notif")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="settings")]
        ]
        
        await self.safe_edit_message(
            query,
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def validate_all_settings(self, query):
        """Kiểm tra tính hợp lệ của tất cả cài đặt"""
        await query.answer("🔍 Đang kiểm tra cài đặt...", show_alert=False)
        
        errors = self.settings_manager.validate_settings()
        
        if not errors:
            result_text = (
                "✅ **Kiểm tra cài đặt hoàn tất**\n\n"
                "🎉 Tất cả cài đặt đều hợp lệ!\n"
                "Bot đang hoạt động với cấu hình tối ưu."
            )
        else:
            result_text = (
                "⚠️ **Phát hiện vấn đề trong cài đặt**\n\n"
                "📋 **Danh sách lỗi:**\n"
            )
            for i, error in enumerate(errors, 1):
                result_text += f"{i}. {error}\n"
            
            result_text += "\n💡 Vui lòng sửa các lỗi trên để bot hoạt động tốt nhất."
        
        keyboard = [
            [
                InlineKeyboardButton("🔧 Sửa tự động", callback_data="settings_auto_fix"),
                InlineKeyboardButton("📖 Hướng dẫn", callback_data="settings_help")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="settings")]
        ]
        
        await self.safe_edit_message(
            query,
            result_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ---------- Utility methods ----------

    async def show_backup_settings(self, query):
        """Hiển thị cài đặt backup"""
        backup_settings = self.settings_manager.get_category("backup")
        
        def bool_icon(val: bool) -> str:
            return "✅" if val else "❌"
        
        settings_text = (
            f"💾 **Cài đặt Backup**\n\n"
            f"🔄 **Tự động backup:** {bool_icon(backup_settings.get('auto_backup_enabled', False))}\n"
            f"⏰ **Chu kỳ backup:** {backup_settings.get('backup_interval_hours', 24)} giờ\n"
            f"📁 **Số file tối đa:** {backup_settings.get('max_backup_files', 10)}\n"
            f"📍 **Thư mục backup:** {backup_settings.get('backup_location', './backups/')}\n"
            f"🖼️ **Bao gồm media:** {bool_icon(backup_settings.get('include_media', False))}\n\n"
            f"⚙️ **Chọn cài đặt để thay đổi:**"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Auto backup", callback_data="settings_toggle_auto_backup"),
                InlineKeyboardButton("⏰ Chu kỳ", callback_data="settings_set_backup_interval")
            ],
            [
                InlineKeyboardButton("📁 Max files", callback_data="settings_set_max_backups"),
                InlineKeyboardButton("🖼️ Media", callback_data="settings_toggle_backup_media")
            ],
            [
                InlineKeyboardButton("💾 Backup ngay", callback_data="settings_backup_now"),
                InlineKeyboardButton("📋 Xem backups", callback_data="settings_list_backups")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="settings")]
        ]
        
        await self.safe_edit_message(
            query,
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_security_settings(self, query):
        """Hiển thị cài đặt bảo mật"""
        security_settings = self.settings_manager.get_category("security")
        
        def bool_icon(val: bool) -> str:
            return "✅" if val else "❌"
        
        settings_text = (
            f"🔒 **Cài đặt Bảo mật**\n\n"
            f"👤 **Chỉ admin:** {bool_icon(security_settings.get('admin_only_mode', True))}\n"
            f"⏰ **Thời gian ban:** {security_settings.get('ban_duration_hours', 24)} giờ\n"
            f"⚠️ **Tối đa cảnh báo:** {security_settings.get('max_warnings', 3)}\n"
            f"🚫 **Tự động ban:** {bool_icon(security_settings.get('auto_ban_on_max_warnings', True))}\n"
            f"✅ **Yêu cầu duyệt:** {bool_icon(security_settings.get('require_admin_approval', False))}\n"
            f"📝 **Log tất cả:** {bool_icon(security_settings.get('log_all_actions', True))}\n\n"
            f"⚙️ **Chọn cài đặt để thay đổi:**"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("👤 Admin only", callback_data="settings_toggle_admin_only"),
                InlineKeyboardButton("⏰ Ban time", callback_data="settings_set_ban_duration")
            ],
            [
                InlineKeyboardButton("⚠️ Max warnings", callback_data="settings_set_max_warnings"),
                InlineKeyboardButton("🚫 Auto ban", callback_data="settings_toggle_auto_ban")
            ],
            [
                InlineKeyboardButton("✅ Duyệt", callback_data="settings_toggle_approval"),
                InlineKeyboardButton("📝 Logging", callback_data="settings_toggle_logging")
            ],
            [
                InlineKeyboardButton("🔄 Reset", callback_data="settings_reset_security"),
                InlineKeyboardButton("📊 Thống kê", callback_data="settings_security_stats")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="settings")]
        ]
        
        await self.safe_edit_message(
            query,
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_interface_settings(self, query):
        """Hiển thị cài đặt giao diện"""
        interface_settings = self.settings_manager.get_category("interface")
        
        def bool_icon(val: bool) -> str:
            return "✅" if val else "❌"
        
        settings_text = (
            f"🎨 **Cài đặt Giao diện**\n\n"
            f"🌍 **Ngôn ngữ:** {interface_settings.get('language', 'vi')}\n"
            f"📄 **Số item/trang:** {interface_settings.get('pagination_size', 5)}\n"
            f"📊 **Hiện thống kê kênh:** {bool_icon(interface_settings.get('show_channel_stats', True))}\n"
            f"👁️ **Xem trước bài đăng:** {bool_icon(interface_settings.get('show_post_previews', True))}\n"
            # f"😊 **Phím tắt emoji:** {bool_icon(interface_settings.get('emoji_shortcuts_enabled', True))}\n"
            f"📱 **Mini app:** {bool_icon(interface_settings.get('mini_app_enabled', True))}\n\n"
            f"⚙️ **Chọn cài đặt để thay đổi:**"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🌍 Ngôn ngữ", callback_data="settings_set_language"),
                InlineKeyboardButton("📄 Phân trang", callback_data="settings_set_pagination")
            ],
            [
                InlineKeyboardButton("📊 Thống kê", callback_data="settings_toggle_channel_stats"),
                InlineKeyboardButton("👁️ Preview", callback_data="settings_toggle_post_previews")
            ],
            [

                InlineKeyboardButton("📱 Mini app", callback_data="settings_toggle_mini_app")
            ],
            [
                InlineKeyboardButton("🔄 Reset", callback_data="settings_reset_interface"),
                InlineKeyboardButton("🎨 Theme", callback_data="settings_theme_options")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="settings")]
        ]
        
        await self.safe_edit_message(
            query,
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_advanced_settings(self, query):
        """Hiển thị cài đặt nâng cao"""
        advanced_settings = self.settings_manager.get_category("advanced")
        
        def bool_icon(val: bool) -> str:
            return "✅" if val else "❌"
        
        settings_text = (
            f"🔧 **Cài đặt Nâng cao**\n\n"
            f"🐛 **Debug mode:** {bool_icon(advanced_settings.get('debug_mode', False))}\n"
            f"📝 **Verbose logging:** {bool_icon(advanced_settings.get('verbose_logging', False))}\n"
            f"📄 **Log file:** {advanced_settings.get('log_file', 'bot.log')}\n"
            f"📊 **Log level:** {advanced_settings.get('log_level', 'INFO')}\n"
            f"⏱️ **API timeout:** {advanced_settings.get('api_timeout', 30)} giây\n"
            f"🔄 **Retry thất bại:** {bool_icon(advanced_settings.get('retry_failed_posts', True))}\n"
            f"🔁 **Max retry:** {advanced_settings.get('max_retry_attempts', 3)}\n\n"
            f"⚙️ **Chọn cài đặt để thay đổi:**"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🐛 Debug", callback_data="settings_toggle_debug"),
                InlineKeyboardButton("📝 Verbose", callback_data="settings_toggle_verbose")
            ],
            [
                InlineKeyboardButton("📊 Log level", callback_data="settings_set_log_level"),
                InlineKeyboardButton("⏱️ Timeout", callback_data="settings_set_api_timeout")
            ],
            [
                InlineKeyboardButton("🔄 Retry", callback_data="settings_toggle_retry"),
                InlineKeyboardButton("🔁 Max retry", callback_data="settings_set_max_retry")
            ],
            [
                InlineKeyboardButton("📄 View logs", callback_data="settings_view_logs"),
                InlineKeyboardButton("🗑️ Clear logs", callback_data="settings_clear_logs")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="settings")]
        ]
        
        await self.safe_edit_message(
            query,
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_export_import_settings(self, query):
        """Hiển thị tùy chọn xuất/nhập cài đặt"""
        export_text = (
            f"📤 **Xuất/Nhập Cài đặt**\n\n"
            f"💾 **Xuất cài đặt hiện tại ra file JSON để sao lưu hoặc chia sẻ**\n"
            f"📥 **Nhập cài đặt từ file JSON để khôi phục**\n\n"
            f"⚠️ **Lưu ý:** Nhập cài đặt sẽ ghi đè toàn bộ cài đặt hiện tại!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📤 Xuất cài đặt", callback_data="settings_export_now"),
                InlineKeyboardButton("📥 Nhập cài đặt", callback_data="settings_import_prompt")
            ],
            [
                InlineKeyboardButton("💾 Backup toàn bộ", callback_data="settings_full_backup"),
                InlineKeyboardButton("🔄 Khôi phục", callback_data="settings_restore_options")
            ],
            [
                InlineKeyboardButton("📋 Xem JSON", callback_data="settings_view_json"),
                InlineKeyboardButton("✅ Validate", callback_data="settings_validate_current")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="settings")]
        ]
        
        await self.safe_edit_message(
            query,
            export_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_set_setting(self, query, action: str):
        """Xử lý đặt giá trị cài đặt"""
        setting_key = action.replace("set_", "")
        
        # Mapping các settings key và thông báo tương ứng
        setting_prompts = {
            "delay": "⏱️ Nhập delay giữa các bài đăng (giây, 1-10):",
            "max_channels": "📊 Nhập số kênh tối đa mỗi lần đăng (1-100):",
            "scheduler_interval": "🔄 Nhập interval kiểm tra scheduler (giây, 10-300):",
            "cleanup_days": "🗑️ Nhập số ngày tự động dọn dẹp (1-365):",
            "max_schedules": "📊 Nhập số lịch đăng tối đa (1-1000):",
            "backup_interval": "⏰ Nhập chu kỳ backup (giờ, 1-168):",
            "max_backups": "📁 Nhập số file backup tối đa (1-50):",
            "ban_duration": "⏰ Nhập thời gian ban (giờ, 1-8760):",
            "max_warnings": "⚠️ Nhập số cảnh báo tối đa (1-10):",
            "pagination": "📄 Nhập số item mỗi trang (3-20):",
            "api_timeout": "⏱️ Nhập timeout API (giây, 10-120):",
            "max_retry": "🔁 Nhập số lần retry tối đa (1-10):",
            "language": "🌍 Chọn ngôn ngữ (vi/en/zh):",
            "log_level": "📊 Chọn log level (DEBUG/INFO/WARNING/ERROR):",
            "timezone": "🌍 Nhập timezone (VD: Asia/Ho_Chi_Minh):"
        }
        
        prompt = setting_prompts.get(setting_key, f"Nhập giá trị cho {setting_key}:")
        
        # Lưu context để xử lý response
        user_id = query.from_user.id
        self.user_states[user_id] = {
            'action': 'setting_input',
            'setting_key': setting_key,
            'original_query': query
        }
        
        keyboard = [[InlineKeyboardButton("❌ Hủy", callback_data="settings")]]
        
        await self.safe_edit_message(
            query,
            f"⚙️ **Thay đổi cài đặt**\n\n{prompt}\n\n📝 Vui lòng gửi giá trị mới:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def toggle_setting(self, query, action: str):
        """Bật/tắt cài đặt boolean"""
        setting_info = {
            "toggle_preview": ("bot", "disable_web_page_preview"),
            "toggle_notification": ("bot", "default_notification"),
            "toggle_protect": ("bot", "default_protect_content"),
            "toggle_rate_limit": ("bot", "rate_limit_enabled"),
            "toggle_parse_mode": ("bot", "default_parse_mode"),
            "toggle_repeat": ("scheduler", "enable_repeat_posts"),
            "toggle_admin_notif": ("notifications", "admin_notifications"),
            "toggle_success_notif": ("notifications", "post_success_notifications"),
            "toggle_failure_notif": ("notifications", "post_failure_notifications"),
            "toggle_channel_notif": ("notifications", "channel_status_notifications"),
            "toggle_scheduler_notif": ("notifications", "scheduler_notifications"),
            "toggle_error_notif": ("notifications", "error_notifications"),
            "toggle_auto_backup": ("backup", "auto_backup_enabled"),
            "toggle_backup_media": ("backup", "include_media"),
            "toggle_admin_only": ("security", "admin_only_mode"),
            "toggle_auto_ban": ("security", "auto_ban_on_max_warnings"),
            "toggle_approval": ("security", "require_admin_approval"),
            "toggle_logging": ("security", "log_all_actions"),
            "toggle_channel_stats": ("interface", "show_channel_stats"),
            "toggle_post_previews": ("interface", "show_post_previews"),

            "toggle_mini_app": ("interface", "mini_app_enabled"),
            "toggle_debug": ("advanced", "debug_mode"),
            "toggle_verbose": ("advanced", "verbose_logging"),
            "toggle_retry": ("advanced", "retry_failed_posts")
        }
        
        if action in setting_info:
            category, key = setting_info[action]
            current_value = self.settings_manager.get_setting(category, key, False)
            
            # Xử lý đặc biệt cho parse_mode
            if key == "default_parse_mode":
                new_value = "HTML" if current_value == "Markdown" else "Markdown"
            else:
                new_value = not current_value
            
            self.settings_manager.set_setting(category, key, new_value)
            
            # Hiển thị lại trang cài đặt tương ứng
            if category == "bot":
                await self.show_bot_settings(query)
            elif category == "scheduler":
                await self.show_scheduler_settings(query)
            elif category == "notifications":
                await self.show_notification_settings(query)
            elif category == "backup":
                await self.show_backup_settings(query)
            elif category == "security":
                await self.show_security_settings(query)
            elif category == "interface":
                await self.show_interface_settings(query)
            elif category == "advanced":
                await self.show_advanced_settings(query)
        else:
            await query.answer("❌ Cài đặt không hợp lệ!", show_alert=True)

    async def confirm_reset_all_settings(self, query):
        """Xác nhận reset tất cả cài đặt"""
        confirm_text = (
            f"⚠️ **Cảnh báo**\n\n"
            f"Bạn có chắc chắn muốn **reset tất cả cài đặt** về mặc định?\n\n"
            f"✅ **Thao tác này không thể hoàn tác!**\n"
            f"💾 **Khuyến khích tạo backup trước khi reset**"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("💾 Backup trước", callback_data="settings_backup_then_reset"),
                InlineKeyboardButton("🚨 Reset ngay", callback_data="settings_confirm_reset")
            ],
            [InlineKeyboardButton("❌ Hủy bỏ", callback_data="settings")]
        ]
        
        await self.safe_edit_message(
            query,
            confirm_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    def _validate_category_settings(self, category: str, settings: dict) -> dict:
        """Validate cài đặt theo category"""
        try:
            if category == "bot":
                # Validate bot settings
                delay = settings.get("delay_between_posts", 2)
                max_channels = settings.get("max_channels_per_post", 50)
                
                if not (1 <= delay <= 10):
                    return {"valid": False, "message": f"Delay không hợp lệ: {delay}"}
                if not (1 <= max_channels <= 100):
                    return {"valid": False, "message": f"Max channels không hợp lệ: {max_channels}"}
                    
            elif category == "scheduler":
                # Validate scheduler settings
                interval = settings.get("check_interval", 30)
                cleanup_days = settings.get("auto_cleanup_days", 30)
                
                if not (10 <= interval <= 300):
                    return {"valid": False, "message": f"Interval không hợp lệ: {interval}"}
                if not (1 <= cleanup_days <= 365):
                    return {"valid": False, "message": f"Cleanup days không hợp lệ: {cleanup_days}"}
            
            # Thêm validation cho các category khác...
            
            return {"valid": True, "message": "Hợp lệ"}
            
        except Exception as e:
            return {"valid": False, "message": f"Lỗi kiểm tra: {str(e)}"}

    async def handle_bulk_notification_toggle(self, query, action: str):
        """Xử lý bật/tắt tất cả thông báo"""
        enable_all = action.startswith("enable_all_notif")
        
        # Danh sách tất cả settings thông báo
        notification_keys = [
            "admin_notifications",
            "post_success_notifications", 
            "post_failure_notifications",
            "channel_status_notifications",
            "scheduler_notifications",
            "error_notifications"
        ]
        
        # Cập nhật tất cả
        for key in notification_keys:
            self.settings_manager.set_setting("notifications", key, enable_all)
        
        action_text = "bật" if enable_all else "tắt"
        await query.answer(f"✅ Đã {action_text} tất cả thông báo!", show_alert=True)
        
        # Refresh trang thông báo
        await self.show_notification_settings(query)

    async def handle_settings_action(self, query, action: str):
        """Xử lý các hành động cài đặt đặc biệt"""
        try:
            if action == "backup_now":
                # Tạo backup ngay
                backup_path = self.settings_manager.create_backup()
                if backup_path:
                    await query.answer(f"✅ Đã tạo backup: {backup_path}", show_alert=True)
                else:
                    await query.answer("❌ Không thể tạo backup!", show_alert=True)
                await self.show_backup_settings(query)
                
            elif action == "export_now":
                # Xuất cài đặt
                export_path = self.settings_manager.export_settings()
                if export_path:
                    await query.answer(f"✅ Đã xuất cài đặt: {export_path}", show_alert=True)
                else:
                    await query.answer("❌ Không thể xuất cài đặt!", show_alert=True)
                await self.show_export_import_settings(query)
                
            elif action == "confirm_reset":
                # Reset tất cả cài đặt
                self.settings_manager.reset_all_settings()
                await query.answer("✅ Đã reset tất cả cài đặt về mặc định!", show_alert=True)
                await self.show_settings(query)
                
            else:
                await query.answer("🚧 Chức năng đang phát triển!", show_alert=False)
                
        except Exception as e:
            await query.answer(f"❌ Lỗi: {str(e)}", show_alert=True)

    async def process_setting_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý input cài đặt từ người dùng"""
        if not update.message or not update.message.text:
            return
        
        user_id = self.check_user_and_admin(update)
        if user_id is None:
            return
        
        state = self.user_states.get(user_id, {})
        setting_key = state.get('setting_key')
        
        if not setting_key:
            return
        
        input_value = update.message.text.strip()
        
        try:
            # Validate và convert giá trị
            validated_value = self._validate_setting_input(setting_key, input_value)
            
            if validated_value is None:
                await update.message.reply_text(
                    f"❌ Giá trị không hợp lệ cho cài đặt {setting_key}!\n"
                    f"Vui lòng thử lại với giá trị đúng định dạng.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Lưu cài đặt
            success = self._save_setting_by_key(setting_key, validated_value)
            
            if success:
                await update.message.reply_text(
                    f"✅ Đã cập nhật cài đặt {setting_key} = {validated_value}",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Xóa state và quay về menu cài đặt
                if user_id in self.user_states:
                    del self.user_states[user_id]
                
                # Hiển thị lại menu cài đặt tương ứng
                await self._show_appropriate_settings_menu(update, setting_key)
            else:
                await update.message.reply_text(
                    f"❌ Không thể lưu cài đặt {setting_key}!",
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            await update.message.reply_text(
                f"❌ Lỗi khi xử lý cài đặt: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    def _validate_setting_input(self, setting_key: str, input_value: str):
        """Validate input value cho setting"""
        try:
            if setting_key in ["delay", "max_channels", "scheduler_interval", "cleanup_days", 
                             "max_schedules", "backup_interval", "max_backups", "ban_duration", 
                             "max_warnings", "pagination", "api_timeout", "max_retry"]:
                # Numeric settings
                value = int(input_value)
                
                # Validate ranges
                ranges = {
                    "delay": (1, 10),
                    "max_channels": (1, 100),
                    "scheduler_interval": (10, 300),
                    "cleanup_days": (1, 365),
                    "max_schedules": (1, 1000),
                    "backup_interval": (1, 168),
                    "max_backups": (1, 50),
                    "ban_duration": (1, 8760),
                    "max_warnings": (1, 10),
                    "pagination": (3, 20),
                    "api_timeout": (10, 120),
                    "max_retry": (1, 10)
                }
                
                min_val, max_val = ranges.get(setting_key, (0, 999999))
                if not (min_val <= value <= max_val):
                    return None
                    
                return value
                
            elif setting_key == "language":
                if input_value.lower() in ["vi", "en", "zh"]:
                    return input_value.lower()
                return None
                
            elif setting_key == "log_level":
                if input_value.upper() in ["DEBUG", "INFO", "WARNING", "ERROR"]:
                    return input_value.upper()
                return None
                
            elif setting_key == "timezone":
                # Basic timezone validation
                if len(input_value) > 3 and "/" in input_value:
                    return input_value
                return None
                
            else:
                return input_value
                
        except (ValueError, TypeError):
            return None

    def _save_setting_by_key(self, setting_key: str, value) -> bool:
        """Lưu cài đặt theo key"""
        try:
            # Mapping setting key to category and field
            setting_mapping = {
                "delay": ("bot", "delay_between_posts"),
                "max_channels": ("bot", "max_channels_per_post"),
                "scheduler_interval": ("scheduler", "check_interval"),
                "cleanup_days": ("scheduler", "auto_cleanup_days"),
                "max_schedules": ("scheduler", "max_scheduled_posts"),
                "backup_interval": ("backup", "backup_interval_hours"),
                "max_backups": ("backup", "max_backup_files"),
                "ban_duration": ("security", "ban_duration_hours"),
                "max_warnings": ("security", "max_warnings"),
                "pagination": ("interface", "pagination_size"),
                "api_timeout": ("advanced", "api_timeout"),
                "max_retry": ("advanced", "max_retry_attempts"),
                "language": ("interface", "language"),
                "log_level": ("advanced", "log_level"),
                "timezone": ("scheduler", "default_timezone")
            }
            
            if setting_key in setting_mapping:
                category, field = setting_mapping[setting_key]
                self.settings_manager.set_setting(category, field, value)
                return True
                
            return False
            
        except Exception as e:
            print(f"Error saving setting {setting_key}: {e}")
            return False

    async def _show_appropriate_settings_menu(self, update: Update, setting_key: str):
        """Hiển thị lại menu cài đặt phù hợp"""
        try:
            # Determine which settings menu to show based on setting_key
            menu_mapping = {
                "delay": "bot", "max_channels": "bot",
                "scheduler_interval": "scheduler", "cleanup_days": "scheduler", 
                "max_schedules": "scheduler", "timezone": "scheduler",
                "backup_interval": "backup", "max_backups": "backup",
                "ban_duration": "security", "max_warnings": "security",
                "pagination": "interface", "language": "interface",
                "api_timeout": "advanced", "max_retry": "advanced", "log_level": "advanced"
            }
            
            menu_type = menu_mapping.get(setting_key, "main")
            
            # Create a mock query object for the menu functions
            class MockQuery:
                def __init__(self, message):
                    self.message = message
                    
                async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                    await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            
            mock_query = MockQuery(update.message)
            
            if menu_type == "bot":
                await self.show_bot_settings(mock_query)
            elif menu_type == "scheduler":
                await self.show_scheduler_settings(mock_query)
            elif menu_type == "backup":
                await self.show_backup_settings(mock_query)
            elif menu_type == "security":
                await self.show_security_settings(mock_query)
            elif menu_type == "interface":
                await self.show_interface_settings(mock_query)
            elif menu_type == "advanced":
                await self.show_advanced_settings(mock_query)
            else:
                await self.show_settings(mock_query)
                
        except Exception as e:
            print(f"Error showing settings menu: {e}")

if __name__ == "__main__":
    # Lấy token từ config
    from config import Config
    
    if not Config.BOT_TOKEN:
        print("❌ Lỗi: Không tìm thấy BOT_TOKEN trong config!")
        exit(1)
    
    if not Config.ADMIN_IDS:
        print("⚠️ Cảnh báo: Không có admin nào được cấu hình!")
        print("Thêm user ID vào Config.ADMIN_IDS để sử dụng bot")
    
    bot = MassPostBot(Config.BOT_TOKEN)
    bot.run() 