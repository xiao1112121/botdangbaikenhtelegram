#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import os
from typing import Dict, List, Optional, Tuple
import unicodedata

class EmojiHandler:
    """Xử lý emoji cho bot Telegram"""
    
    def __init__(self):
        self.emoji_mapping = self._load_emoji_mapping()
        self.unicode_emoji_patterns = self._load_unicode_patterns()
        
    def _load_emoji_mapping(self) -> Dict[str, str]:
        """Tải mapping emoji từ text sang Unicode"""
        return {
            # Emoji cơ bản
            ':)': '😊',
            ':-)': '😊',
            ':(': '😢',
            ':-(': '😢',
            ':D': '😃',
            ':-D': '😃',
            ':P': '😛',
            ':-P': '😛',
            ';)': '😉',
            ';-)': '😉',
            ':o': '😮',
            ':-o': '😮',
            ':*': '😘',
            ':-*': '😘',
            '<3': '❤️',
            '</3': '💔',
            
            # Emoji phổ biến cho đăng bài
            '[fire]': '🔥',
            '[rocket]': '🚀',
            '[star]': '⭐',
            '[heart]': '❤️',
            '[thumbsup]': '👍',
            '[thumbsdown]': '👎',
            '[clap]': '👏',
            '[money]': '💰',
            '[dollar]': '💵',
            '[sale]': '🏷️',
            '[new]': '🆕',
            '[hot]': '🔥',
            '[cool]': '😎',
            '[ok]': '✅',
            '[no]': '❌',
            '[warning]': '⚠️',
            '[info]': 'ℹ️',
            '[question]': '❓',
            '[exclamation]': '❗',
            '[light]': '💡',
            '[target]': '🎯',
            '[gift]': '🎁',
            '[crown]': '👑',
            '[diamond]': '💎',
            '[gem]': '💍',
            '[clock]': '⏰',
            '[calendar]': '📅',
            '[phone]': '📱',
            '[computer]': '💻',
            '[email]': '📧',
            '[link]': '🔗',
            '[globe]': '🌐',
            '[location]': '📍',
            '[home]': '🏠',
            '[office]': '🏢',
            '[shop]': '🏪',
            '[food]': '🍔',
            '[coffee]': '☕',
            '[car]': '🚗',
            '[plane]': '✈️',
            '[train]': '🚂',
            '[ship]': '🚢',
            '[music]': '🎵',
            '[movie]': '🎬',
            '[game]': '🎮',
            '[book]': '📚',
            '[pen]': '✏️',
            '[camera]': '📷',
            '[mic]': '🎤',
            '[speaker]': '📢',
            '[bell]': '🔔',
            '[key]': '🔑',
            '[lock]': '🔒',
            '[unlock]': '🔓',
            '[shield]': '🛡️',
            '[sword]': '⚔️',
            '[magic]': '✨',
            '[rainbow]': '🌈',
            '[sun]': '☀️',
            '[moon]': '🌙',
            '[stars]': '⭐',
            '[cloud]': '☁️',
            '[rain]': '🌧️',
            '[snow]': '❄️',
            '[flower]': '🌸',
            '[tree]': '🌳',
            '[leaf]': '🍃',
            '[grass]': '🌱',
            '[mountain]': '⛰️',
            '[ocean]': '🌊',
            '[fire_emoji]': '🔥',
            '[ice]': '🧊',
            '[earth]': '🌍',
            '[space]': '🚀',
            '[alien]': '👽',
            '[robot]': '🤖',
            '[ghost]': '👻',
            '[skull]': '💀',
            '[poop]': '💩',
            '[devil]': '😈',
            '[angel]': '😇',
            '[party]': '🎉',
            '[birthday]': '🎂',
            '[christmas]': '🎄',
            '[halloween]': '🎃',
            '[valentine]': '💕',
            '[wedding]': '💒',
            '[baby]': '👶',
            '[child]': '🧒',
            '[adult]': '🧑',
            '[elder]': '🧓',
            '[man]': '👨',
            '[woman]': '👩',
            '[boy]': '👦',
            '[girl]': '👧',
            '[family]': '👨‍👩‍👧‍👦',
            '[couple]': '👫',
            '[friends]': '👭',
            '[team]': '👥',
            '[boss]': '👔',
            '[worker]': '👷',
            '[doctor]': '👨‍⚕️',
            '[teacher]': '👨‍🏫',
            '[student]': '👨‍🎓',
            '[artist]': '👨‍🎨',
            '[chef]': '👨‍🍳',
            '[farmer]': '👨‍🌾',
            '[police]': '👮',
            '[soldier]': '👨‍✈️',
            '[pilot]': '👨‍✈️',
            '[astronaut]': '👨‍🚀',
            '[scientist]': '👨‍🔬',
            '[programmer]': '👨‍💻',
            '[singer]': '👨‍🎤',
            '[dancer]': '💃',
            '[athlete]': '🏃',
            '[winner]': '🏆',
            '[medal]': '🏅',
            '[flag]': '🏴',
            '[vietnam]': '🇻🇳',
            '[usa]': '🇺🇸',
            '[china]': '🇨🇳',
            '[japan]': '🇯🇵',
            '[korea]': '🇰🇷',
            '[uk]': '🇬🇧',
            '[france]': '🇫🇷',
            '[germany]': '🇩🇪',
            '[italy]': '🇮🇹',
            '[spain]': '🇪🇸',
            '[russia]': '🇷🇺',
            '[brazil]': '🇧🇷',
            '[australia]': '🇦🇺',
            '[canada]': '🇨🇦',
            '[india]': '🇮🇳',
            '[thailand]': '🇹🇭',
            '[singapore]': '🇸🇬',
            '[malaysia]': '🇲🇾',
            '[indonesia]': '🇮🇩',
            '[philippines]': '🇵🇭',
        }
    
    def _load_unicode_patterns(self) -> List[str]:
        """Tải các pattern Unicode emoji"""
        return [
            r'[\U0001F600-\U0001F64F]',  # Emoticons
            r'[\U0001F300-\U0001F5FF]',  # Symbols & Pictographs
            r'[\U0001F680-\U0001F6FF]',  # Transport & Map
            r'[\U0001F1E0-\U0001F1FF]',  # Flags (iOS)
            r'[\U00002702-\U000027B0]',  # Dingbats
            r'[\U000024C2-\U0001F251]',  # Enclosed characters
            r'[\U0001F900-\U0001F9FF]',  # Supplemental Symbols and Pictographs
            r'[\U0001FA70-\U0001FAFF]',  # Symbols and Pictographs Extended-A
        ]
    
    def process_text_with_emoji(self, text: str) -> str:
        """Xử lý text, chuyển đổi emoji shortcodes thành Unicode"""
        if not text:
            return text
        
        # Chuyển đổi emoji shortcodes
        processed_text = text
        for shortcode, emoji in self.emoji_mapping.items():
            processed_text = processed_text.replace(shortcode, emoji)
        
        # Xử lý emoji bị lỗi từ desktop
        processed_text = self._fix_broken_emoji(processed_text)
        
        return processed_text
    
    def _fix_broken_emoji(self, text: str) -> str:
        """Sửa emoji bị lỗi từ Telegram Desktop"""
        # Xử lý emoji bị encode sai
        try:
            # Thử decode lại nếu text bị encode sai
            if '\\u' in text:
                text = text.encode().decode('unicode_escape')
            
            # Xử lý emoji bị hiển thị dưới dạng � hoặc □
            text = re.sub(r'[�□]', '❓', text)
            
            # Xử lý emoji compound bị tách
            text = self._fix_compound_emoji(text)
            
        except Exception as e:
            print(f"Lỗi khi xử lý emoji: {e}")
        
        return text
    
    def _fix_compound_emoji(self, text: str) -> str:
        """Sửa emoji phức hợp bị tách"""
        # Các emoji phức hợp phổ biến
        compound_fixes = {
            '👨 💻': '👨‍💻',
            '👩 💻': '👩‍💻',
            '👨 🍳': '👨‍🍳',
            '👩 🍳': '👩‍🍳',
            '👨 ⚕️': '👨‍⚕️',
            '👩 ⚕️': '👩‍⚕️',
            '👨 🎓': '👨‍🎓',
            '👩 🎓': '👩‍🎓',
            '👨 🏫': '👨‍🏫',
            '👩 🏫': '👩‍🏫',
            '👨 🎨': '👨‍🎨',
            '👩 🎨': '👩‍🎨',
            '👨 🚀': '👨‍🚀',
            '👩 🚀': '👩‍🚀',
            '👨 🚒': '👨‍🚒',
            '👩 🚒': '👩‍🚒',
            '👨 ✈️': '👨‍✈️',
            '👩 ✈️': '👩‍✈️',
            '👨 💼': '👨‍💼',
            '👩 💼': '👩‍💼',
            '👨 🔧': '👨‍🔧',
            '👩 🔧': '👩‍🔧',
            '👨 🌾': '👨‍🌾',
            '👩 🌾': '👩‍🌾',
            '👨 🍼': '👨‍🍼',
            '👩 🍼': '👩‍🍼',
            '👨 ⚖️': '👨‍⚖️',
            '👩 ⚖️': '👩‍⚖️',
            '👨 🦲': '👨‍🦲',
            '👩 🦲': '👩‍🦲',
            '👨 🦱': '👨‍🦱',
            '👩 🦱': '👩‍🦱',
            '👨 🦰': '👨‍🦰',
            '👩 🦰': '👩‍🦰',
            '👨 🦳': '👨‍🦳',
            '👩 🦳': '👩‍🦳',
        }
        
        for broken, fixed in compound_fixes.items():
            text = text.replace(broken, fixed)
        
        return text
    
    def extract_emoji_from_text(self, text: str) -> List[str]:
        """Trích xuất tất cả emoji từ text"""
        if not text:
            return []
        
        emoji_list = []
        
        # Sử dụng regex để tìm emoji
        for pattern in self.unicode_emoji_patterns:
            matches = re.findall(pattern, text)
            emoji_list.extend(matches)
        
        return list(set(emoji_list))  # Loại bỏ duplicate
    
    def clean_text_from_emoji(self, text: str) -> str:
        """Xóa emoji khỏi text"""
        if not text:
            return text
        
        cleaned_text = text
        for pattern in self.unicode_emoji_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text)
        
        return cleaned_text.strip()
    
    def get_emoji_keyboard(self, category: str = "popular") -> List[List[str]]:
        """Tạo emoji keyboard cho inline"""
        emoji_categories = {
            "popular": [
                "😊", "😂", "❤️", "👍", "👏", "🔥", "💯", "✨",
                "🚀", "⭐", "💰", "🎉", "🎁", "💎", "👑", "🏆",
                "📱", "💻", "🌟", "🎯", "💡", "⚡", "🌈", "🔔"
            ],
            "business": [
                "💼", "📊", "💰", "💵", "💳", "💲", "🏢", "🏪",
                "📈", "📉", "💹", "🎯", "💡", "⚡", "🔥", "🚀",
                "⭐", "🌟", "✨", "💎", "👑", "🏆", "🥇", "🎁"
            ],
            "social": [
                "👥", "👫", "👪", "💬", "💭", "📢", "📣", "📢",
                "👍", "👎", "👏", "🤝", "💪", "🙌", "✊", "👊",
                "❤️", "💕", "💖", "💗", "💘", "💝", "💐", "🌹"
            ],
            "food": [
                "🍔", "🍕", "🍟", "🌭", "🥪", "🌮", "🌯", "🥗",
                "🍜", "🍝", "🍱", "🍣", "🍤", "🍙", "🍘", "🍚",
                "🍛", "🥘", "🍲", "🥟", "🍳", "🥞", "🧇", "🥓"
            ],
            "transport": [
                "🚗", "🚙", "🚐", "🚛", "🚜", "🏎️", "🚓", "🚔",
                "🚑", "🚒", "🚐", "🛻", "🚚", "🚛", "🚜", "🏎️",
                "🚲", "🛴", "🛵", "🏍️", "✈️", "🚀", "🛸", "🚁"
            ],
            "nature": [
                "🌱", "🌿", "🍀", "🌾", "🌵", "🌴", "🌳", "🌲",
                "🌸", "🌺", "🌻", "🌷", "🌹", "🥀", "🌼", "🌿",
                "🌞", "🌝", "🌛", "🌜", "🌚", "🌕", "🌖", "🌗"
            ],
            "objects": [
                "📱", "💻", "⌨️", "🖥️", "🖨️", "📷", "📹", "📼",
                "🎥", "📞", "☎️", "📠", "📧", "📩", "📨", "📫",
                "📬", "📭", "📮", "🗳️", "✏️", "✒️", "🖋️", "🖊️"
            ],
            "symbols": [
                "❤️", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
                "❣️", "💕", "💖", "💗", "💘", "💝", "💟", "☮️",
                "✝️", "☪️", "🕉️", "☸️", "✡️", "🔯", "🕎", "☯️"
            ]
        }
        
        category_emoji = emoji_categories.get(category, emoji_categories["popular"])
        
        # Tạo keyboard 4 cột
        keyboard = []
        for i in range(0, len(category_emoji), 4):
            row = category_emoji[i:i+4]
            keyboard.append(row)
        
        return keyboard
    
    def get_emoji_picker_text(self) -> str:
        """Tạo text cho emoji picker"""
        return """
🎨 **Emoji Picker**

**Cách sử dụng:**
1. Chọn emoji từ bàn phím bên dưới
2. Hoặc gõ shortcode: `[fire]` → 🔥
3. Hoặc copy emoji từ danh sách:

**📢 Phổ biến:**
🔥 🚀 ⭐ ❤️ 👍 👏 💰 💯 ✨ 🎉 🎁 💎 👑 🏆

**💼 Kinh doanh:**
💼 📊 💰 💵 💳 💲 🏢 🏪 📈 📉 💹 🎯 💡 ⚡

**👥 Xã hội:**
👥 👫 👪 💬 💭 📢 📣 👍 👎 👏 🤝 💪 🙌

**🎯 Hành động:**
✅ ❌ ⚠️ ℹ️ ❓ ❗ 💡 🎯 🔔 📢 📣 🚨 🔥 💥

**Gõ /cancel để hủy**
        """
    
    def validate_emoji_in_text(self, text: str) -> Tuple[bool, List[str]]:
        """Kiểm tra và validate emoji trong text"""
        if not text:
            return True, []
        
        issues = []
        
        # Kiểm tra emoji bị lỗi
        if '�' in text or '□' in text:
            issues.append("Phát hiện emoji bị lỗi hiển thị")
        
        # Kiểm tra emoji quá nhiều
        emoji_count = len(self.extract_emoji_from_text(text))
        if emoji_count > 20:
            issues.append(f"Quá nhiều emoji ({emoji_count}), nên dùng ít hơn 20")
        
        # Kiểm tra text chỉ toàn emoji
        clean_text = self.clean_text_from_emoji(text)
        if len(clean_text.strip()) == 0 and emoji_count > 0:
            issues.append("Bài viết chỉ có emoji, nên thêm text")
        
        return len(issues) == 0, issues
    
    def suggest_emoji_for_text(self, text: str) -> List[str]:
        """Gợi ý emoji phù hợp với nội dung text"""
        if not text:
            return []
        
        text_lower = text.lower()
        suggestions = []
        
        # Từ khóa và emoji tương ứng
        keyword_emoji = {
            # Kinh doanh
            ('sale', 'giảm giá', 'khuyến mãi', 'ưu đãi'): ['🏷️', '💸', '🎁', '💰'],
            ('money', 'tiền', 'thu nhập', 'lương'): ['💰', '💵', '💳', '💲'],
            ('business', 'kinh doanh', 'doanh nghiệp'): ['💼', '🏢', '📊', '📈'],
            ('success', 'thành công', 'chiến thắng'): ['🏆', '🥇', '👑', '✨'],
            ('new', 'mới', 'ra mắt', 'launch'): ['🆕', '🚀', '⭐', '🌟'],
            
            # Cảm xúc
            ('happy', 'vui', 'hạnh phúc', 'vui vẻ'): ['😊', '😂', '🎉', '😍'],
            ('love', 'yêu', 'thích', 'tình yêu'): ['❤️', '💕', '💖', '😍'],
            ('angry', 'tức giận', 'bực mình'): ['😠', '💢', '😤', '👿'],
            ('sad', 'buồn', 'tủi thân'): ['😢', '😭', '💔', '😞'],
            ('excited', 'hứng thú', 'phấn khích'): ['🎉', '🎊', '🚀', '✨'],
            # Hành động
            ('buy', 'mua', 'shopping', 'mua sắm'): ['🛒', '🛍️', '💳', '🏪'],
            ('sell', 'bán', 'selling'): ['🏷️', '💰', '📢', '🏪'],
            ('call', 'gọi', 'liên hệ'): ['📞', '☎️', '📱', '📧'],
            ('visit', 'đến', 'ghé thăm'): ['🏠', '🏢', '📍', '🗺️'],
            ('learn', 'học', 'học tập'): ['📚', '🎓', '📖', '💡'],
            ('work', 'làm việc', 'công việc'): ['💼', '👔', '🏢', '💻'],
            
            # Thời gian
            ('today', 'hôm nay', 'ngày hôm nay'): ['📅', '⏰', '🌅', '☀️'],
            ('tomorrow', 'ngày mai', 'mai'): ['📅', '🌅', '⏰', '🚀'],
            ('now', 'bây giờ', 'hiện tại'): ['⏰', '🔔', '📢', '💨'],
            ('time', 'thời gian', 'giờ'): ['⏰', '⏱️', '📅', '🕐'],
            
            # Địa điểm
            ('home', 'nhà', 'gia đình'): ['🏠', '🏡', '👨‍👩‍👧‍👦', '❤️'],
            ('office', 'văn phòng', 'công ty'): ['🏢', '💼', '👔', '💻'],
            ('restaurant', 'nhà hàng', 'quán ăn'): ['🍽️', '🍔', '🏪', '👨‍🍳'],
            ('school', 'trường học', 'học'): ['🏫', '📚', '🎓', '✏️'],
            
            # Thể loại
            ('food', 'đồ ăn', 'món ăn'): ['🍔', '🍕', '🍜', '🥘'],
            ('drink', 'đồ uống', 'nước'): ['☕', '🥤', '🍺', '🍷'],
            ('tech', 'công nghệ', 'technology'): ['💻', '📱', '⚙️', '🤖'],
            ('game', 'trò chơi', 'gaming'): ['🎮', '🕹️', '🎯', '🏆'],
            ('music', 'âm nhạc', 'nhạc'): ['🎵', '🎶', '🎤', '🎧'],
            ('movie', 'phim', 'cinema'): ['🎬', '🎭', '🍿', '🎪'],
            ('travel', 'du lịch', 'travel'): ['✈️', '🏖️', '🗺️', '📷'],
            ('sport', 'thể thao', 'sports'): ['⚽', '🏀', '🏆', '🥇'],
            ('car', 'xe', 'ô tô'): ['🚗', '🚙', '🏎️', '🚗'],
            ('phone', 'điện thoại', 'mobile'): ['📱', '☎️', '📞', '📧'],
        }
        
        # Tìm emoji phù hợp
        for keywords, emojis in keyword_emoji.items():
            for keyword in keywords:
                if keyword in text_lower:
                    suggestions.extend(emojis)
        
        # Loại bỏ duplicate và giới hạn
        suggestions = list(set(suggestions))[:8]
        
        # Nếu không có gợi ý, trả về emoji phổ biến
        if not suggestions:
            suggestions = ['😊', '👍', '🔥', '⭐', '💯', '✨', '🚀', '❤️']
        
        return suggestions
    
    def count_emoji_in_text(self, text: str) -> Dict[str, int]:
        """Đếm số lượng emoji trong text"""
        if not text:
            return {}
        
        emoji_list = self.extract_emoji_from_text(text)
        emoji_count = {}
        
        for emoji in emoji_list:
            emoji_count[emoji] = text.count(emoji)
        
        return emoji_count
    
    def get_emoji_help_text(self) -> str:
        """Trả về text hướng dẫn sử dụng emoji"""
        return """
🎨 **Hướng dẫn sử dụng Emoji**

**🔧 Cách nhập emoji:**
1. **Shortcode**: Gõ `[fire]` → 🔥
2. **Copy-paste**: Copy emoji từ web/mobile
3. **Emoji picker**: Dùng /emoji để chọn

**⚠️ Xử lý lỗi Telegram Desktop:**
- Emoji bị hiển thị `�` hoặc `□` → Bot tự động sửa
- Emoji phức hợp bị tách → Bot tự động ghép lại
- Emoji không hiển thị → Dùng shortcode thay thế

**💡 Mẹo sử dụng:**
- Không dùng quá 20 emoji trong 1 bài
- Cân bằng giữa emoji và text
- Dùng emoji phù hợp với nội dung
- Test trước khi đăng hàng loạt

**📝 Shortcode phổ biến:**
`[fire]` → 🔥, `[rocket]` → 🚀, `[star]` → ⭐
`[heart]` → ❤️, `[thumbsup]` → 👍, `[money]` → 💰
`[new]` → 🆕, `[hot]` → 🔥, `[cool]` → 😎
`[ok]` → ✅, `[no]` → ❌, `[warning]` → ⚠️

**🔍 Kiểm tra emoji:**
Bot sẽ tự động:
- Sửa emoji bị lỗi
- Gợi ý emoji phù hợp
- Cảnh báo nếu quá nhiều emoji
- Validate trước khi đăng

Gõ /emoji để mở emoji picker!
        """

# Tạo instance global
emoji_handler = EmojiHandler()

# Convenience functions
def process_emoji(text: str) -> str:
    return emoji_handler.process_text_with_emoji(text)

def validate_emoji(text: str) -> Tuple[bool, List[str]]:
    return emoji_handler.validate_emoji_in_text(text)

def suggest_emoji(text: str) -> List[str]:
    return emoji_handler.suggest_emoji_for_text(text)

def get_emoji_keyboard(category: str = "popular") -> List[List[str]]:
    return emoji_handler.get_emoji_keyboard(category)

def clean_emoji(text: str) -> str:
    return emoji_handler.clean_text_from_emoji(text) 