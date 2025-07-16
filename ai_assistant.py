#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class AIAssistant:
    """AI Assistant để hỗ trợ người dùng tạo nội dung và tối ưu hóa"""
    
    def __init__(self):
        self.content_patterns = self._load_content_patterns()
        self.engagement_keywords = self._load_engagement_keywords()
        self.spam_indicators = self._load_spam_indicators()
        self.optimal_times = self._load_optimal_times()
    
    def _load_content_patterns(self) -> Dict[str, List[str]]:
        """Tải các mẫu nội dung hiệu quả"""
        return {
            "marketing": [
                "🔥 SALE HOT - Giảm {discount}% tất cả sản phẩm!",
                "⏰ CHỈ CÒN {time} - Cơ hội cuối để sở hữu {product}",
                "🎁 QUÀ TẶNG ĐẶC BIỆT cho {number} khách hàng đầu tiên!",
                "💎 SIÊU PHẨM mới - {product} vừa ra mắt!",
                "🏆 ĐƯỢC CHỌN bởi hơn {number} khách hàng tin tùng!"
            ],
            "announcement": [
                "📢 THÔNG BÁO QUAN TRỌNG: {content}",
                "🔔 CẬP NHẬT MỚI: {content}",
                "⚠️ LƯU Ý: {content}",
                "✅ XÁC NHẬN: {content}",
                "📋 HƯỚNG DẪN: {content}"
            ],
            "engagement": [
                "💬 Hãy cho chúng tôi biết ý kiến của bạn!",
                "🤔 Bạn nghĩ sao về {topic}?",
                "👇 Comment ngay để {action}!",
                "🔗 Share để {benefit}!",
                "❤️ React nếu bạn đồng ý!"
            ],
            "educational": [
                "💡 TIP HAY: {tip}",
                "📚 KIẾN THỨC: {knowledge}",
                "🎯 BÍ QUYẾT: {secret}",
                "📖 HƯỚNG DẪN: {guide}",
                "🔍 PHÂN TÍCH: {analysis}"
            ]
        }
    
    def _load_engagement_keywords(self) -> Dict[str, int]:
        """Từ khóa tăng engagement"""
        return {
            # Action words
            "sale": 5, "giảm giá": 5, "free": 4, "miễn phí": 4,
            "hot": 3, "nóng": 3, "new": 3, "mới": 3,
            "limited": 4, "giới hạn": 4, "exclusive": 4, "độc quyền": 4,
            
            # Emotional words
            "amazing": 3, "tuyệt vời": 3, "incredible": 3, "không thể tin": 3,
            "shocking": 4, "gây sốc": 4, "surprising": 3, "bất ngờ": 3,
            
            # Urgency words
            "now": 3, "ngay": 3, "today": 3, "hôm nay": 3,
            "hurry": 4, "nhanh lên": 4, "last chance": 5, "cơ hội cuối": 5,
            
            # Social proof
            "popular": 3, "phổ biến": 3, "trending": 4, "xu hướng": 4,
            "bestseller": 4, "bán chạy": 4, "recommended": 3, "khuyến nghị": 3
        }
    
    def _load_spam_indicators(self) -> Dict[str, int]:
        """Chỉ số phát hiện spam"""
        return {
            # Excessive caps
            "excessive_caps": 8,  # Quá nhiều chữ in hoa
            "multiple_exclamations": 6,  # Nhiều dấu !!!
            "repeated_emojis": 5,  # Emoji lặp lại
            "suspicious_links": 9,  # Link đáng ngờ
            "money_symbols": 7,  # Nhiều ký hiệu tiền
            "urgent_language": 6,  # Ngôn ngữ cấp bách quá mức
            "fake_scarcity": 8,  # Tạo khan hiếm giả
            "misleading_claims": 9,  # Tuyên bố sai lệch
        }
    
    def _load_optimal_times(self) -> Dict[str, List[int]]:
        """Thời gian đăng bài tối ưu"""
        return {
            "general": [9, 12, 15, 18, 21],  # Giờ tổng quát
            "business": [9, 10, 14, 16],  # Nội dung kinh doanh
            "entertainment": [19, 20, 21, 22],  # Giải trí
            "news": [7, 8, 12, 18],  # Tin tức
            "educational": [10, 14, 16, 20]  # Giáo dục
        }
    
    def suggest_content_improvement(self, content: str, post_type: str = "general") -> Dict[str, Any]:
        """Gợi ý cải thiện nội dung"""
        suggestions = {
            "score": 0,
            "improvements": [],
            "enhanced_content": content,
            "engagement_potential": "medium"
        }
        
        # Phân tích độ dài
        content_length = len(content)
        if content_length < 50:
            suggestions["improvements"].append("📝 Nội dung hơi ngắn, hãy thêm chi tiết để thu hút hơn")
        elif content_length > 1000:
            suggestions["improvements"].append("✂️ Nội dung hơi dài, hãy rút gọn để dễ đọc hơn")
        else:
            suggestions["score"] += 2
        
        # Kiểm tra emoji
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content))
        if emoji_count == 0:
            suggestions["improvements"].append("😊 Thêm emoji để nội dung sinh động hơn")
        elif emoji_count > 10:
            suggestions["improvements"].append("😅 Giảm bớt emoji để tránh rối mắt")
        else:
            suggestions["score"] += 1
        
        # Kiểm tra từ khóa engagement
        engagement_score = 0
        for keyword, score in self.engagement_keywords.items():
            if keyword.lower() in content.lower():
                engagement_score += score
        
        suggestions["score"] += min(engagement_score, 10)
        
        # Gợi ý từ khóa
        if engagement_score < 5:
            suggested_keywords = random.sample(list(self.engagement_keywords.keys()), 3)
            suggestions["improvements"].append(f"🎯 Thêm từ khóa hấp dẫn: {', '.join(suggested_keywords)}")
        
        # Kiểm tra call-to-action
        cta_patterns = ["comment", "share", "like", "follow", "mua", "đăng ký", "liên hệ"]
        has_cta = any(pattern in content.lower() for pattern in cta_patterns)
        if not has_cta:
            suggestions["improvements"].append("📢 Thêm lời kêu gọi hành động (call-to-action)")
        else:
            suggestions["score"] += 2
        
        # Đánh giá tổng thể
        if suggestions["score"] >= 8:
            suggestions["engagement_potential"] = "high"
        elif suggestions["score"] >= 5:
            suggestions["engagement_potential"] = "medium"
        else:
            suggestions["engagement_potential"] = "low"
        
        # Tạo enhanced content
        suggestions["enhanced_content"] = self._enhance_content(content, post_type)
        
        return suggestions
    
    def _enhance_content(self, content: str, post_type: str) -> str:
        """Nâng cao nội dung tự động"""
        enhanced = content
        
        # Thêm emoji phù hợp
        if not re.search(r'[\U0001F600-\U0001F64F]', enhanced):
            if post_type == "marketing":
                enhanced = "🔥 " + enhanced
            elif post_type == "announcement":
                enhanced = "📢 " + enhanced
            elif post_type == "educational":
                enhanced = "💡 " + enhanced
        
        # Thêm hashtag nếu chưa có
        if "#" not in enhanced:
            if post_type == "marketing":
                enhanced += "\n\n#Sale #Promotion #Deal"
            elif post_type == "educational":
                enhanced += "\n\n#Tips #Learning #Knowledge"
        
        return enhanced
    
    def detect_spam_content(self, content: str) -> Dict[str, Any]:
        """Phát hiện nội dung spam"""
        spam_score = 0
        issues = []
        
        # Kiểm tra quá nhiều chữ hoa
        caps_ratio = sum(1 for c in content if c.isupper()) / max(1, len(content))
        if caps_ratio > 0.5:
            spam_score += self.spam_indicators["excessive_caps"]
            issues.append("Quá nhiều chữ IN HOA")
        
        # Kiểm tra dấu chấm than liên tiếp
        exclamation_count = len(re.findall(r'!{3,}', content))
        if exclamation_count > 0:
            spam_score += self.spam_indicators["multiple_exclamations"]
            issues.append("Quá nhiều dấu chấm than liên tiếp")
        
        # Kiểm tra emoji lặp lại
        emoji_pattern = re.findall(r'([\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF])\1{3,}', content)
        if emoji_pattern:
            spam_score += self.spam_indicators["repeated_emojis"]
            issues.append("Emoji lặp lại quá nhiều")
        
        # Kiểm tra link đáng ngờ
        suspicious_domains = ["bit.ly", "tinyurl.com", "t.co", "goo.gl"]
        for domain in suspicious_domains:
            if domain in content.lower():
                spam_score += self.spam_indicators["suspicious_links"]
                issues.append(f"Link rút gọn đáng ngờ: {domain}")
        
        # Kiểm tra ngôn ngữ cấp bách
        urgent_words = ["urgent", "gấp", "nhanh lên", "hết hạn", "limited time", "last chance"]
        urgent_count = sum(1 for word in urgent_words if word.lower() in content.lower())
        if urgent_count > 2:
            spam_score += self.spam_indicators["urgent_language"]
            issues.append("Ngôn ngữ cấp bách quá mức")
        
        return {
            "is_spam": spam_score > 15,
            "spam_score": spam_score,
            "risk_level": "high" if spam_score > 15 else "medium" if spam_score > 8 else "low",
            "issues": issues
        }
    
    def suggest_optimal_time(self, content: str, channel_stats: Optional[Dict] = None) -> Dict[str, Any]:
        """Gợi ý thời gian đăng bài tối ưu"""
        # Phân loại nội dung
        content_type = self._classify_content(content)
        
        # Lấy thời gian tối ưu theo loại
        base_times = self.optimal_times.get(content_type, self.optimal_times["general"])
        
        # Điều chỉnh dựa trên stats kênh
        if channel_stats and "peak_hours" in channel_stats:
            channel_peak_hours = channel_stats["peak_hours"]
            # Kết hợp thời gian tối ưu chung và của kênh
            combined_times = list(set(base_times + channel_peak_hours))
        else:
            combined_times = base_times
        
        # Tính thời gian gần nhất
        now = datetime.now()
        suggestions = []
        
        for hour in sorted(combined_times):
            # Tính thời gian đăng tiếp theo
            next_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)
            
            suggestions.append({
                "time": next_time.strftime("%H:%M"),
                "date": next_time.strftime("%Y-%m-%d"),
                "datetime": next_time.isoformat(),
                "reason": f"Thời gian tối ưu cho nội dung {content_type}"
            })
        
        return {
            "content_type": content_type,
            "suggestions": suggestions[:3],  # Top 3 suggestions
            "next_optimal": suggestions[0] if suggestions else None
        }
    
    def _classify_content(self, content: str) -> str:
        """Phân loại nội dung"""
        content_lower = content.lower()
        
        # Keywords cho từng loại
        business_keywords = ["sale", "giảm giá", "mua", "bán", "sản phẩm", "dịch vụ", "khuyến mãi"]
        entertainment_keywords = ["game", "phim", "nhạc", "fun", "vui", "giải trí", "funny"]
        news_keywords = ["thông báo", "tin tức", "cập nhật", "mới", "breaking", "news"]
        educational_keywords = ["học", "tip", "hướng dẫn", "cách", "guide", "tutorial", "tips"]
        
        # Đếm từ khóa
        business_score = sum(1 for word in business_keywords if word in content_lower)
        entertainment_score = sum(1 for word in entertainment_keywords if word in content_lower)
        news_score = sum(1 for word in news_keywords if word in content_lower)
        educational_score = sum(1 for word in educational_keywords if word in content_lower)
        
        # Trả về loại có điểm cao nhất
        scores = {
            "business": business_score,
            "entertainment": entertainment_score,
            "news": news_score,
            "educational": educational_score
        }
        
        max_score = max(scores.values())
        if max_score == 0:
            return "general"
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def generate_hashtags(self, content: str, max_tags: int = 5) -> List[str]:
        """Tạo hashtag phù hợp"""
        # Từ điển mapping từ khóa -> hashtag
        hashtag_mapping = {
            "sale": ["#Sale", "#Promotion", "#Deal"],
            "giảm giá": ["#Sale", "#GiamGia", "#KhuyenMai"],
            "new": ["#New", "#Latest", "#Fresh"],
            "mới": ["#Moi", "#MoiNhat", "#RaMat"],
            "tip": ["#Tips", "#Advice", "#Guide"],
            "học": ["#Hoc", "#Education", "#Learning"],
            "game": ["#Gaming", "#Game", "#Play"],
            "food": ["#Food", "#Foodie", "#Delicious"],
            "travel": ["#Travel", "#Trip", "#Adventure"]
        }
        
        suggested_tags = []
        content_lower = content.lower()
        
        # Tìm hashtag dựa trên từ khóa
        for keyword, tags in hashtag_mapping.items():
            if keyword in content_lower:
                suggested_tags.extend(tags)
        
        # Loại bỏ duplicate và giới hạn số lượng
        suggested_tags = list(set(suggested_tags))[:max_tags]
        
        # Nếu không đủ, thêm hashtag chung
        if len(suggested_tags) < max_tags:
            general_tags = ["#Post", "#Share", "#Like", "#Follow", "#Content"]
            needed = max_tags - len(suggested_tags)
            suggested_tags.extend(general_tags[:needed])
        
        return suggested_tags
    
    def analyze_engagement_potential(self, content: str, historical_data: Optional[List] = None) -> Dict[str, Any]:
        """Phân tích tiềm năng engagement"""
        analysis = {
            "score": 0,
            "factors": [],
            "predictions": {},
            "recommendations": []
        }
        
        # Phân tích độ dài tối ưu
        length = len(content)
        if 100 <= length <= 300:
            analysis["score"] += 3
            analysis["factors"].append("Độ dài tối ưu")
        elif length < 50:
            analysis["recommendations"].append("Mở rộng nội dung thêm chi tiết")
        elif length > 500:
            analysis["recommendations"].append("Rút gọn nội dung để dễ đọc")
        
        # Phân tích emoji usage
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]', content))
        if 1 <= emoji_count <= 5:
            analysis["score"] += 2
            analysis["factors"].append("Sử dụng emoji phù hợp")
        
        # Phân tích từ khóa engagement
        engagement_words = 0
        for word in self.engagement_keywords:
            if word.lower() in content.lower():
                engagement_words += 1
        
        if engagement_words >= 2:
            analysis["score"] += 2
            analysis["factors"].append("Có từ khóa hấp dẫn")
        
        # Predictions
        analysis["predictions"] = {
            "estimated_reach": min(1000 + analysis["score"] * 100, 5000),
            "estimated_engagement_rate": min(analysis["score"] * 0.5 + 2, 10),
            "best_time_to_post": self.suggest_optimal_time(content)["next_optimal"]
        }
        
        return analysis

# Global instance
ai_assistant = AIAssistant()

def get_content_suggestions(content: str, post_type: str = "general") -> Dict[str, Any]:
    """Shortcut function để lấy gợi ý nội dung"""
    return ai_assistant.suggest_content_improvement(content, post_type)

def check_spam_content(content: str) -> Dict[str, Any]:
    """Shortcut function để kiểm tra spam"""
    return ai_assistant.detect_spam_content(content) 