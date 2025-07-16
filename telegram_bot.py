#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import os
import sys
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from telegram import (
    Bot,
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ChatPermissions,
    Message,
    User
)
import asyncio
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    filters,
    ContextTypes
)

# Import local modules
from config import Config
from database import BotDatabase

# Cấu hình logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Khắc phục lỗi "There is no current event loop" trên Windows + Python 3.11
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# pyright: reportOptionalMemberAccess=false, reportAttributeAccessIssue=false, reportCallIssue=false
class TelegramGroupBot:
    def __init__(self, token: str, application: Optional[Application] = None):
        self.token = token
        # Nếu đã truyền Application từ ngoài, dùng chung; ngược lại tự tạo
        if application is None:
            # Tự động xoá webhook cũ nếu tự khởi tạo application
            try:
                asyncio.run(Bot(token).delete_webhook(drop_pending_updates=True))
            except Exception:
                pass

            try:
                asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())

        self.application = application if application else Application.builder().token(token).build()
        self.db = BotDatabase()
        self.config = Config()
        self.banned_words = Config.BANNED_WORDS
        self.admin_commands = [
            "/kick", "/ban", "/unban", "/mute", "/unmute", 
            "/warn", "/unwarn", "/info", "/rules", "/admin"
        ]
        
        # Thiết lập handlers
        self.setup_handlers()
        self.warnings: Dict[int, int] = {} # Khởi tạo self.warnings
    
    def setup_handlers(self):
        """Thiết lập các handlers cho bot"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("group_admin", self.admin_panel))
        self.application.add_handler(CommandHandler("kick", self.kick_user))
        self.application.add_handler(CommandHandler("ban", self.ban_user))
        self.application.add_handler(CommandHandler("unban", self.unban_user))
        self.application.add_handler(CommandHandler("mute", self.mute_user))
        self.application.add_handler(CommandHandler("unmute", self.unmute_user))
        self.application.add_handler(CommandHandler("warn", self.warn_user))
        self.application.add_handler(CommandHandler("unwarn", self.unwarn_user))
        self.application.add_handler(CommandHandler("info", self.user_info))
        self.application.add_handler(CommandHandler("rules", self.show_rules))
        self.application.add_handler(CommandHandler("group_stats", self.group_stats))
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.check_message))
        self.application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.welcome_new_member))
        self.application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, self.goodbye_member))
        
        # Chat member handler
        self.application.add_handler(ChatMemberHandler(self.track_chat_members, ChatMemberHandler.CHAT_MEMBER))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lệnh /start"""
        if not update.message:
            return
            
        welcome_text = """
🤖 **Xin chào! Tôi là Bot Quản Lý Nhóm**

📋 **Chức năng chính:**
• Quản lý thành viên (kick, ban, mute)
• Hệ thống cảnh báo
• Lọc tin nhắn spam
• Chào mừng thành viên mới
• Thống kê nhóm

🔧 **Lệnh dành cho Admin:**
/admin - Bảng điều khiển admin
/kick - Kick thành viên
/ban - Ban thành viên
/mute - Mute thành viên
/warn - Cảnh báo thành viên
/info - Thông tin thành viên
/rules - Quy tắc nhóm

📊 **Lệnh khác:**
/help - Trợ giúp
/stats - Thống kê nhóm
        """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lệnh /help"""
        help_text = """
📚 **Hướng dẫn sử dụng Bot (Quản lý nhóm)**

**🔧 Lệnh Admin:**
• `/kick [@user]` - Kick thành viên
• `/ban [@user]` - Ban thành viên  
• `/unban [@user]` - Unban thành viên
• `/mute [@user] [thời gian]` - Mute thành viên
• `/unmute [@user]` - Unmute thành viên
• `/warn [@user] [lý do]` - Cảnh báo thành viên
• `/unwarn [@user]` - Hủy cảnh báo
• `/info [@user]` - Thông tin thành viên
• `/group_admin` - Bảng điều khiển admin nhóm

**📊 Lệnh khác:**
• `/rules` - Xem quy tắc nhóm
• `/group_stats` - Thống kê nhóm

**💡 Lưu ý:**
- Chỉ admin mới có thể sử dụng các lệnh quản lý
- Bot sẽ tự động lọc tin nhắn spam
- Thành viên nhận 3 cảnh báo sẽ bị kick
        """
        
        await update.effective_message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bảng điều khiển admin"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("👤 Quản lý thành viên", callback_data="admin_members"),
                InlineKeyboardButton("📝 Quản lý tin nhắn", callback_data="admin_messages")
            ],
            [
                InlineKeyboardButton("⚠️ Cảnh báo", callback_data="admin_warnings"),
                InlineKeyboardButton("📊 Thống kê", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("⚙️ Cài đặt", callback_data="admin_settings"),
                InlineKeyboardButton("📋 Quy tắc", callback_data="admin_rules")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 **Bảng điều khiển Admin**\n\nChọn chức năng bạn muốn sử dụng:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý callback từ inline keyboard"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "admin_members":
            keyboard = [
                [
                    InlineKeyboardButton("👢 Kick thành viên", callback_data="action_kick"),
                    InlineKeyboardButton("🚫 Ban thành viên", callback_data="action_ban")
                ],
                [
                    InlineKeyboardButton("🔇 Mute thành viên", callback_data="action_mute"),
                    InlineKeyboardButton("🔊 Unmute thành viên", callback_data="action_unmute")
                ],
                [InlineKeyboardButton("◀️ Quay lại", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "👤 **Quản lý thành viên**\n\nChọn hành động:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif query.data == "admin_messages":
            keyboard = [
                [
                    InlineKeyboardButton("🗑️ Xóa tin nhắn", callback_data="action_delete"),
                    InlineKeyboardButton("📝 Chỉnh sửa filter", callback_data="action_filter")
                ],
                [InlineKeyboardButton("◀️ Quay lại", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📝 **Quản lý tin nhắn**\n\nChọn hành động:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif query.data == "admin_warnings":
            warnings_text = "⚠️ **Hệ thống cảnh báo**\n\n"
            if self.warnings:
                for user_id, count in self.warnings.items():
                    warnings_text += f"• User {user_id}: {count} cảnh báo\n"
            else:
                warnings_text += "Không có cảnh báo nào."
            
            keyboard = [[InlineKeyboardButton("◀️ Quay lại", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                warnings_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

        elif getattr(query, "data", None) == "back_main":
            await self.admin_panel(update, context)
        user_id = getattr(update.effective_user, "id", None)
        chat_id = getattr(update.effective_chat, "id", None)

        if user_id is None or chat_id is None:
            return False
        
        try:
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            return chat_member.status in ['creator', 'administrator']
        except:
            return False
    
    async def kick_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kick thành viên"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Vui lòng reply tin nhắn của người cần kick hoặc dùng /kick @username")
            return
        
        try:
            if update.message.reply_to_message:
                user_id = update.message.reply_to_message.from_user.id
                username = update.message.reply_to_message.from_user.first_name
            else:
                # Xử lý @username
                username = context.args[0].replace('@', '')
                # Tìm user_id từ username (cần implement thêm)
                await update.message.reply_text("⚠️ Vui lòng reply tin nhắn của người cần kick")
                return
            
            await context.bot.kick_chat_member(update.effective_chat.id, user_id)
            await update.message.reply_text(f"✅ Đã kick {username} khỏi nhóm!")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi khi kick user: {str(e)}")
    
    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban thành viên"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Vui lòng reply tin nhắn của người cần ban!")
            return
        
        try:
            user_id = update.message.reply_to_message.from_user.id
            username = update.message.reply_to_message.from_user.first_name
            
            await context.bot.ban_chat_member(update.effective_chat.id, user_id)
            await update.message.reply_text(f"✅ Đã ban {username} khỏi nhóm!")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi khi ban user: {str(e)}")
    
    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban thành viên"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Vui lòng reply tin nhắn của người cần unban!")
            return
        
        try:
            user_id = update.message.reply_to_message.from_user.id
            username = update.message.reply_to_message.from_user.first_name
            
            await context.bot.unban_chat_member(update.effective_chat.id, user_id)
            await update.message.reply_text(f"✅ Đã unban {username}!")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi khi unban user: {str(e)}")
    
    async def mute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mute thành viên"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Vui lòng reply tin nhắn của người cần mute!")
            return
        
        try:
            user_id = update.message.reply_to_message.from_user.id
            username = update.message.reply_to_message.from_user.first_name
            
            # Mute permissions
            permissions = ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
            
            # Thời gian mute (mặc định 1 giờ)
            mute_time = 60 * 60  # 1 hour
            if context.args:
                try:
                    mute_time = int(context.args[0]) * 60  # phút
                except:
                    pass
            
            until_date = datetime.now() + timedelta(seconds=mute_time)
            
            await context.bot.restrict_chat_member(
                update.effective_chat.id,
                user_id,
                permissions,
                until_date=until_date
            )
            
            await update.message.reply_text(f"🔇 Đã mute {username} trong {mute_time//60} phút!")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi khi mute user: {str(e)}")
    
    async def unmute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unmute thành viên"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Vui lòng reply tin nhắn của người cần unmute!")
            return
        
        try:
            user_id = update.message.reply_to_message.from_user.id
            username = update.message.reply_to_message.from_user.first_name
            
            # Restore permissions
            permissions = ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
            
            await context.bot.restrict_chat_member(
                update.effective_chat.id,
                user_id,
                permissions
            )
            
            await update.message.reply_text(f"🔊 Đã unmute {username}!")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi khi unmute user: {str(e)}")
    
    async def warn_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cảnh báo thành viên"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Vui lòng reply tin nhắn của người cần cảnh báo!")
            return
        
        user_id = update.message.reply_to_message.from_user.id
        username = update.message.reply_to_message.from_user.first_name
        reason = " ".join(context.args) if context.args else "Không có lý do"
        
        # Tăng số cảnh báo
        if user_id not in self.warnings:
            self.warnings[user_id] = 0
        self.warnings[user_id] += 1
        
        warn_count = self.warnings[user_id]
        
        await update.message.reply_text(
            f"⚠️ **Cảnh báo {warn_count}/3** cho {username}\n"
            f"**Lý do:** {reason}\n\n"
            f"{'⚠️ Cảnh báo cuối cùng!' if warn_count == 2 else ''}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Kick nếu đủ 3 cảnh báo
        if warn_count >= 3:
            try:
                await context.bot.kick_chat_member(update.effective_chat.id, user_id)
                await update.message.reply_text(f"🚫 {username} đã bị kick do nhận đủ 3 cảnh báo!")
                del self.warnings[user_id]
            except Exception as e:
                await update.message.reply_text(f"❌ Lỗi khi kick user: {str(e)}")
    
    async def unwarn_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hủy cảnh báo"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Vui lòng reply tin nhắn của người cần hủy cảnh báo!")
            return
        
        user_id = update.message.reply_to_message.from_user.id
        username = update.message.reply_to_message.from_user.first_name
        
        if user_id in self.warnings:
            del self.warnings[user_id]
            await update.message.reply_text(f"✅ Đã hủy tất cả cảnh báo cho {username}!")
        else:
            await update.message.reply_text(f"ℹ️ {username} không có cảnh báo nào!")
    
    async def user_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Thông tin thành viên"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Vui lòng reply tin nhắn của người cần xem thông tin!")
            return
        
        user = update.message.reply_to_message.from_user
        user_id = user.id
        
        # Lấy thông tin chat member
        try:
            chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
            status = chat_member.status
        except:
            status = "unknown"
        
        warnings = self.warnings.get(user_id, 0)
        
        info_text = f"""
👤 **Thông tin thành viên**

**ID:** `{user_id}`
**Tên:** {user.first_name}
**Username:** @{user.username if user.username else 'Không có'}
**Trạng thái:** {status}
**Cảnh báo:** {warnings}/3
**Bot:** {'Có' if user.is_bot else 'Không'}
        """
        
        await update.message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)
    
    async def show_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hiển thị quy tắc nhóm"""
        rules_text = """
📋 **QUY TẮC NHÓM**

1️⃣ **Tôn trọng lẫn nhau** - Không được chửi bới, xúc phạm
2️⃣ **Không spam** - Không gửi tin nhắn liên tục, không quảng cáo
3️⃣ **Nội dung phù hợp** - Không nội dung 18+, bạo lực
4️⃣ **Không off-topic** - Chỉ thảo luận nội dung liên quan
5️⃣ **Không share link rác** - Không chia sẻ link không an toàn

⚠️ **Hình phạt:**
• Cảnh báo 1: Nhắc nhở
• Cảnh báo 2: Mute 1 giờ  
• Cảnh báo 3: Kick khỏi nhóm

🤖 **Liên hệ Admin nếu cần hỗ trợ!**
        """
        
        await update.message.reply_text(rules_text, parse_mode=ParseMode.MARKDOWN)
    
    async def group_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Thống kê nhóm"""
        try:
            chat = await context.bot.get_chat(update.effective_chat.id)
            member_count = await context.bot.get_chat_member_count(update.effective_chat.id)
            
            stats_text = f"""
📊 **THỐNG KÊ NHÓM**

**Tên nhóm:** {chat.title}
**Loại:** {chat.type}
**Thành viên:** {member_count}
**Mô tả:** {chat.description if chat.description else 'Không có'}

⚠️ **Cảnh báo hiện tại:** {len(self.warnings)}
🤖 **Bot hoạt động:** Bình thường
            """
            
            await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi khi lấy thống kê: {str(e)}")
    
    async def check_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kiểm tra tin nhắn có spam không"""
        message_text = update.message.text.lower()
        
        # Kiểm tra từ cấm
        for banned_word in self.banned_words:
            if banned_word in message_text:
                await update.message.delete()
                await update.message.reply_text(
                    f"🚫 Tin nhắn đã bị xóa do chứa nội dung không phù hợp!\n"
                    f"Người gửi: {update.message.from_user.first_name}"
                )
                return
    
    async def welcome_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Chào mừng thành viên mới"""
        for member in update.message.new_chat_members:
            if not member.is_bot:
                welcome_text = f"""
🎉 **Chào mừng {member.first_name} đến với nhóm!**

📋 Vui lòng đọc /rules để tìm hiểu quy tắc nhóm
💬 Hãy tự giới thiệu bản thân nhé!
🤝 Chúc bạn có những trải nghiệm tuyệt vời!
                """
                
                await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    
    async def goodbye_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tạm biệt thành viên rời nhóm"""
        left_member = update.message.left_chat_member
        if not left_member.is_bot:
            await update.message.reply_text(
                f"👋 {left_member.first_name} đã rời khỏi nhóm. Chúc bạn may mắn!"
            )
            
            # Xóa cảnh báo của user
            if left_member.id in self.warnings:
                del self.warnings[left_member.id]
    
    async def track_chat_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Theo dõi thay đổi thành viên"""
        # Có thể implement thêm logging hoặc thống kê
        pass
    
    def run(self):
        """Chạy bot"""
        print("🤖 Bot đang khởi động...")
        print("📱 Nhấn Ctrl+C để dừng bot")

        # Đảm bảo luồng chính có event loop
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        try:
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except KeyboardInterrupt:
            print("\n🛑 Bot đã dừng!")

if __name__ == "__main__":
    # Lấy token thực từ Config
    TOKEN = Config.BOT_TOKEN

    if not TOKEN:
        print("❌ Chưa cấu hình BOT_TOKEN trong Config hoặc .env!")
        exit(1)

    bot = TelegramGroupBot(TOKEN)
    bot.run() 