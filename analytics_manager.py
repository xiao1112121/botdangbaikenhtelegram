#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import statistics
import logging

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """Quản lý thống kê và phân tích dữ liệu bot"""
    
    def __init__(self, analytics_file: str = "analytics_data.json"):
        self.analytics_file = analytics_file
        self.data = self._load_analytics_data()
    
    def _load_analytics_data(self) -> Dict[str, Any]:
        """Tải dữ liệu analytics từ file"""
        default_data = {
            "posts": [],  # Lịch sử tất cả bài đăng
            "channels": {},  # Thống kê theo kênh
            "daily_stats": {},  # Thống kê theo ngày
            "user_activity": {},  # Hoạt động của user
            "performance_metrics": {},  # Metrics hiệu suất
            "errors": [],  # Lịch sử lỗi
            "last_updated": datetime.now().isoformat()
        }
        
        if os.path.exists(self.analytics_file):
            try:
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Merge với default để đảm bảo có đủ keys
                    for key in default_data:
                        if key not in data:
                            data[key] = default_data[key]
                    return data
            except Exception as e:
                logger.error(f"Lỗi khi tải analytics: {e}")
        
        return default_data
    
    def save_analytics_data(self):
        """Lưu dữ liệu analytics"""
        try:
            self.data["last_updated"] = datetime.now().isoformat()
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi lưu analytics: {e}")
    
    def record_post(self, post_data: Dict[str, Any]):
        """Ghi nhận một bài đăng mới"""
        post_record = {
            "id": post_data.get("id", str(len(self.data["posts"]))),
            "timestamp": datetime.now().isoformat(),
            "type": post_data.get("type", "text"),
            "channels": post_data.get("channels", []),
            "success_count": post_data.get("success_count", 0),
            "failure_count": post_data.get("failure_count", 0),
            "content_length": len(post_data.get("content", "")),
            "has_media": post_data.get("has_media", False),
            "has_buttons": post_data.get("has_buttons", False),
            "user_id": post_data.get("user_id"),
            "scheduled": post_data.get("scheduled", False)
        }
        
        self.data["posts"].append(post_record)
        self._update_daily_stats(post_record)
        self._update_channel_stats(post_record)
        self._update_user_activity(post_record)
        self.save_analytics_data()
    
    def record_error(self, error_data: Dict[str, Any]):
        """Ghi nhận lỗi"""
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "type": error_data.get("type", "unknown"),
            "message": error_data.get("message", ""),
            "channel_id": error_data.get("channel_id"),
            "user_id": error_data.get("user_id"),
            "context": error_data.get("context", {})
        }
        
        self.data["errors"].append(error_record)
        
        # Giữ chỉ 1000 lỗi gần nhất
        if len(self.data["errors"]) > 1000:
            self.data["errors"] = self.data["errors"][-1000:]
        
        self.save_analytics_data()
    
    def _update_daily_stats(self, post_record: Dict[str, Any]):
        """Cập nhật thống kê theo ngày"""
        date_key = post_record["timestamp"][:10]  # YYYY-MM-DD
        
        if date_key not in self.data["daily_stats"]:
            self.data["daily_stats"][date_key] = {
                "total_posts": 0,
                "successful_posts": 0,
                "failed_posts": 0,
                "total_channels_reached": 0,
                "post_types": defaultdict(int),
                "peak_hour": defaultdict(int)
            }
        
        stats = self.data["daily_stats"][date_key]
        stats["total_posts"] += 1
        stats["successful_posts"] += post_record["success_count"]
        stats["failed_posts"] += post_record["failure_count"]
        stats["total_channels_reached"] += len(post_record["channels"])
        stats["post_types"][post_record["type"]] += 1
        
        # Cập nhật giờ peak
        hour = int(post_record["timestamp"][11:13])
        stats["peak_hour"][str(hour)] += 1
    
    def _update_channel_stats(self, post_record: Dict[str, Any]):
        """Cập nhật thống kê theo kênh"""
        for channel_id in post_record["channels"]:
            if channel_id not in self.data["channels"]:
                self.data["channels"][channel_id] = {
                    "total_posts": 0,
                    "successful_posts": 0,
                    "failed_posts": 0,
                    "last_post": None,
                    "avg_response_time": 0,
                    "post_types": defaultdict(int),
                    "peak_days": defaultdict(int)
                }
            
            stats = self.data["channels"][channel_id]
            stats["total_posts"] += 1
            stats["last_post"] = post_record["timestamp"]
            stats["post_types"][post_record["type"]] += 1
            
            # Cập nhật ngày trong tuần
            weekday = datetime.fromisoformat(post_record["timestamp"]).weekday()
            stats["peak_days"][str(weekday)] += 1
    
    def _update_user_activity(self, post_record: Dict[str, Any]):
        """Cập nhật hoạt động người dùng"""
        user_id = str(post_record.get("user_id", "unknown"))
        
        if user_id not in self.data["user_activity"]:
            self.data["user_activity"][user_id] = {
                "total_posts": 0,
                "successful_posts": 0,
                "failed_posts": 0,
                "first_post": post_record["timestamp"],
                "last_post": post_record["timestamp"],
                "favorite_post_type": "text",
                "most_active_hour": "12"
            }
        
        activity = self.data["user_activity"][user_id]
        activity["total_posts"] += 1
        activity["successful_posts"] += post_record["success_count"]
        activity["failed_posts"] += post_record["failure_count"]
        activity["last_post"] = post_record["timestamp"]
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """Lấy thống kê tổng quan"""
        total_posts = len(self.data["posts"])
        if total_posts == 0:
            return {
                "total_posts": 0,
                "success_rate": 0,
                "active_channels": 0,
                "total_users": 0,
                "avg_posts_per_day": 0
            }
        
        total_success = sum(post["success_count"] for post in self.data["posts"])
        total_attempts = sum(post["success_count"] + post["failure_count"] for post in self.data["posts"])
        success_rate = (total_success / total_attempts * 100) if total_attempts > 0 else 0
        
        # Kênh hoạt động (có bài đăng trong 7 ngày qua)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        active_channels = len([
            ch for ch, stats in self.data["channels"].items()
            if stats.get("last_post", "") > week_ago
        ])
        
        return {
            "total_posts": total_posts,
            "success_rate": round(success_rate, 2),
            "active_channels": active_channels,
            "total_users": len(self.data["user_activity"]),
            "avg_posts_per_day": self._calculate_avg_posts_per_day()
        }
    
    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Lấy thống kê theo ngày"""
        stats = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_stats = self.data["daily_stats"].get(date, {
                "total_posts": 0,
                "successful_posts": 0,
                "failed_posts": 0,
                "total_channels_reached": 0
            })
            day_stats["date"] = date
            stats.append(day_stats)
        
        return list(reversed(stats))
    
    def get_channel_performance(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy hiệu suất top channels"""
        channels = []
        
        for channel_id, stats in self.data["channels"].items():
            if stats["total_posts"] > 0:
                success_rate = (stats["successful_posts"] / stats["total_posts"] * 100)
                channels.append({
                    "channel_id": channel_id,
                    "total_posts": stats["total_posts"],
                    "success_rate": round(success_rate, 2),
                    "last_post": stats["last_post"]
                })
        
        # Sắp xếp theo success rate và total posts
        channels.sort(key=lambda x: (x["success_rate"], x["total_posts"]), reverse=True)
        return channels[:limit]
    
    def get_post_type_distribution(self) -> Dict[str, int]:
        """Lấy phân bố loại bài đăng"""
        distribution = defaultdict(int)
        for post in self.data["posts"]:
            distribution[post["type"]] += 1
        return dict(distribution)
    
    def get_peak_hours(self) -> List[Tuple[int, int]]:
        """Lấy giờ cao điểm đăng bài"""
        hour_counts = defaultdict(int)
        
        for post in self.data["posts"]:
            hour = int(post["timestamp"][11:13])
            hour_counts[hour] += 1
        
        # Trả về top 5 giờ cao điểm
        return sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def get_error_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Phân tích lỗi"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        recent_errors = [
            error for error in self.data["errors"]
            if error["timestamp"] > cutoff_date
        ]
        
        error_types = Counter(error["type"] for error in recent_errors)
        error_channels = Counter(
            error["channel_id"] for error in recent_errors
            if error.get("channel_id")
        )
        
        return {
            "total_errors": len(recent_errors),
            "error_types": dict(error_types.most_common(5)),
            "problematic_channels": dict(error_channels.most_common(5)),
            "error_rate": len(recent_errors) / max(1, len(self.data["posts"][-100:])) * 100
        }
    
    def _calculate_avg_posts_per_day(self) -> float:
        """Tính trung bình bài đăng mỗi ngày"""
        if not self.data["posts"]:
            return 0
        
        # Lấy 30 ngày gần nhất
        recent_days = list(self.data["daily_stats"].keys())[-30:]
        if not recent_days:
            return 0
        
        total_posts = sum(
            self.data["daily_stats"][day]["total_posts"]
            for day in recent_days
        )
        
        return round(total_posts / len(recent_days), 2)
    
    def generate_insights(self) -> List[str]:
        """Tạo insights tự động"""
        insights = []
        
        # Insight về success rate
        overview = self.get_overview_stats()
        if overview["success_rate"] < 80:
            insights.append(f"⚠️ Tỷ lệ thành công {overview['success_rate']}% thấp hơn mong đợi")
        elif overview["success_rate"] > 95:
            insights.append(f"🎉 Tỷ lệ thành công {overview['success_rate']}% rất tốt!")
        
        # Insight về peak hours
        peak_hours = self.get_peak_hours()
        if peak_hours:
            best_hour = peak_hours[0][0]
            insights.append(f"📊 Giờ đăng bài hiệu quả nhất: {best_hour}:00")
        
        # Insight về post types
        post_types = self.get_post_type_distribution()
        if post_types:
            most_popular = max(post_types.items(), key=lambda x: x[1])
            insights.append(f"📈 Loại bài đăng phổ biến nhất: {most_popular[0]}")
        
        # Insight về channels
        channel_perf = self.get_channel_performance(5)
        if channel_perf:
            best_channel = channel_perf[0]
            insights.append(f"🏆 Kênh hiệu suất cao nhất: {best_channel['success_rate']}% thành công")
        
        return insights
    
    def export_analytics_report(self, format: str = "json") -> str:
        """Xuất báo cáo analytics"""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "overview": self.get_overview_stats(),
            "daily_stats": self.get_daily_stats(30),
            "channel_performance": self.get_channel_performance(20),
            "post_type_distribution": self.get_post_type_distribution(),
            "peak_hours": self.get_peak_hours(),
            "error_analysis": self.get_error_analysis(30),
            "insights": self.generate_insights()
        }
        
        filename = f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        
        try:
            if format == "json":
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
            else:
                # Có thể thêm support cho CSV, PDF sau
                pass
                
            logger.info(f"Đã xuất báo cáo analytics: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Lỗi khi xuất báo cáo: {e}")
            return ""
    
    def cleanup_old_data(self, days: int = 90):
        """Dọn dẹp dữ liệu cũ"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Xóa posts cũ
        self.data["posts"] = [
            post for post in self.data["posts"]
            if post["timestamp"] > cutoff_date
        ]
        
        # Xóa daily stats cũ
        old_dates = [
            date for date in self.data["daily_stats"].keys()
            if date < cutoff_date[:10]
        ]
        for date in old_dates:
            del self.data["daily_stats"][date]
        
        # Xóa errors cũ
        self.data["errors"] = [
            error for error in self.data["errors"]
            if error["timestamp"] > cutoff_date
        ]
        
        self.save_analytics_data()
        logger.info(f"Đã dọn dẹp dữ liệu cũ hơn {days} ngày") 