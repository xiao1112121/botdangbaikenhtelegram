#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib
import mimetypes
import logging

logger = logging.getLogger(__name__)

class TemplateManager:
    """Quản lý template bài đăng và media library"""
    
    def __init__(self, templates_file: str = "templates.json", media_dir: str = "media_library"):
        self.templates_file = templates_file
        self.media_dir = Path(media_dir)
        self.media_dir.mkdir(exist_ok=True)
        
        # Tạo các thư mục con
        (self.media_dir / "images").mkdir(exist_ok=True)
        (self.media_dir / "videos").mkdir(exist_ok=True)
        (self.media_dir / "documents").mkdir(exist_ok=True)
        (self.media_dir / "audio").mkdir(exist_ok=True)
        
        self.templates = self._load_templates()
        self.media_index = self._load_media_index()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Tải danh sách template"""
        default_data = {
            "templates": [],
            "categories": ["Marketing", "Announcement", "Educational", "Entertainment", "General"],
            "last_updated": datetime.now().isoformat()
        }
        
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Lỗi khi tải templates: {e}")
        
        return default_data
    
    def _load_media_index(self) -> Dict[str, Any]:
        """Tải index của media library"""
        index_file = self.media_dir / "media_index.json"
        default_index = {
            "files": [],
            "tags": {},
            "stats": {
                "total_files": 0,
                "total_size": 0,
                "last_cleanup": datetime.now().isoformat()
            }
        }
        
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Lỗi khi tải media index: {e}")
        
        return default_index
    
    def save_templates(self):
        """Lưu templates"""
        try:
            self.templates["last_updated"] = datetime.now().isoformat()
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi lưu templates: {e}")
    
    def save_media_index(self):
        """Lưu media index"""
        try:
            index_file = self.media_dir / "media_index.json"
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.media_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi lưu media index: {e}")
    
    # ============ TEMPLATE MANAGEMENT ============
    
    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo template mới"""
        template = {
            "id": self._generate_template_id(),
            "name": template_data.get("name", "Untitled Template"),
            "category": template_data.get("category", "General"),
            "description": template_data.get("description", ""),
            "content": {
                "type": template_data.get("type", "text"),
                "text": template_data.get("text", ""),
                "media_id": template_data.get("media_id"),
                "buttons": template_data.get("buttons", []),
                "settings": {
                    "disable_web_page_preview": template_data.get("disable_preview", False),
                    "disable_notification": template_data.get("disable_notification", False),
                    "protect_content": template_data.get("protect_content", False)
                }
            },
            "variables": template_data.get("variables", []),  # Biến có thể thay thế
            "tags": template_data.get("tags", []),
            "usage_count": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "created_by": template_data.get("user_id")
        }
        
        self.templates["templates"].append(template)
        self.save_templates()
        
        logger.info(f"Đã tạo template mới: {template['name']}")
        return {
            "success": True,
            "template_id": template["id"],
            "message": f"Đã tạo template '{template['name']}' thành công"
        }
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Cập nhật template"""
        template = self.get_template(template_id)
        if not template:
            return {"success": False, "message": "Không tìm thấy template"}
        
        # Cập nhật các trường
        for key, value in updates.items():
            if key in template:
                template[key] = value
            elif key in template["content"]:
                template["content"][key] = value
        
        template["updated_at"] = datetime.now().isoformat()
        self.save_templates()
        
        return {"success": True, "message": "Đã cập nhật template thành công"}
    
    def delete_template(self, template_id: str) -> Dict[str, Any]:
        """Xóa template"""
        template_index = None
        for i, template in enumerate(self.templates["templates"]):
            if template["id"] == template_id:
                template_index = i
                break
        
        if template_index is None:
            return {"success": False, "message": "Không tìm thấy template"}
        
        deleted_template = self.templates["templates"].pop(template_index)
        self.save_templates()
        
        return {
            "success": True,
            "message": f"Đã xóa template '{deleted_template['name']}' thành công"
        }
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Lấy template theo ID"""
        for template in self.templates["templates"]:
            if template["id"] == template_id:
                return template
        return None
    
    def list_templates(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Liệt kê templates với filter"""
        templates = self.templates["templates"]
        
        # Filter theo category
        if category and category != "All":
            templates = [t for t in templates if t["category"] == category]
        
        # Filter theo tags
        if tags:
            templates = [
                t for t in templates
                if any(tag in t.get("tags", []) for tag in tags)
            ]
        
        # Sắp xếp theo usage_count và updated_at
        return sorted(templates, key=lambda x: (x["usage_count"], x["updated_at"]), reverse=True)
    
    def use_template(self, template_id: str, variables: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Sử dụng template với variables"""
        template = self.get_template(template_id)
        if not template:
            return {"success": False, "message": "Không tìm thấy template"}
        
        # Tăng usage count
        template["usage_count"] += 1
        template["last_used"] = datetime.now().isoformat()
        
        # Thay thế variables
        content = template["content"].copy()
        if variables and content.get("text"):
            text = content["text"]
            for var, value in variables.items():
                text = text.replace(f"{{{var}}}", value)
            content["text"] = text
        
        self.save_templates()
        
        return {
            "success": True,
            "content": content,
            "template_name": template["name"]
        }
    
    def _generate_template_id(self) -> str:
        """Tạo ID duy nhất cho template"""
        return f"tpl_{int(datetime.now().timestamp())}_{len(self.templates['templates'])}"
    
    # ============ MEDIA LIBRARY ============
    
    def add_media(self, file_path: str, filename: str, tags: List[str] = None, description: str = "") -> Dict[str, Any]:
        """Thêm file media vào library"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return {"success": False, "message": "File không tồn tại"}
            
            # Xác định loại file
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                if mime_type.startswith('image/'):
                    media_type = 'images'
                elif mime_type.startswith('video/'):
                    media_type = 'videos'
                elif mime_type.startswith('audio/'):
                    media_type = 'audio'
                else:
                    media_type = 'documents'
            else:
                media_type = 'documents'
            
            # Tạo hash của file để tránh duplicate
            file_hash = self._calculate_file_hash(source_path)
            
            # Kiểm tra duplicate
            for media_file in self.media_index["files"]:
                if media_file["hash"] == file_hash:
                    return {"success": False, "message": "File đã tồn tại trong library"}
            
            # Copy file vào media directory
            media_id = self._generate_media_id()
            file_extension = source_path.suffix
            new_filename = f"{media_id}{file_extension}"
            destination = self.media_dir / media_type / new_filename
            
            shutil.copy2(source_path, destination)
            
            # Thêm vào index
            media_record = {
                "id": media_id,
                "original_name": filename,
                "stored_name": new_filename,
                "type": media_type,
                "mime_type": mime_type,
                "size": source_path.stat().st_size,
                "hash": file_hash,
                "tags": tags or [],
                "description": description,
                "uploaded_at": datetime.now().isoformat(),
                "usage_count": 0,
                "last_used": None
            }
            
            self.media_index["files"].append(media_record)
            
            # Cập nhật tags index
            for tag in (tags or []):
                if tag not in self.media_index["tags"]:
                    self.media_index["tags"][tag] = []
                self.media_index["tags"][tag].append(media_id)
            
            # Cập nhật stats
            self.media_index["stats"]["total_files"] += 1
            self.media_index["stats"]["total_size"] += source_path.stat().st_size
            
            self.save_media_index()
            
            logger.info(f"Đã thêm media: {filename} -> {media_id}")
            return {
                "success": True,
                "media_id": media_id,
                "message": f"Đã thêm {filename} vào media library"
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi thêm media: {e}")
            return {"success": False, "message": f"Lỗi: {str(e)}"}
    
    def get_media(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin media"""
        for media_file in self.media_index["files"]:
            if media_file["id"] == media_id:
                return media_file
        return None
    
    def get_media_path(self, media_id: str) -> Optional[Path]:
        """Lấy đường dẫn file media"""
        media = self.get_media(media_id)
        if not media:
            return None
        
        return self.media_dir / media["type"] / media["stored_name"]
    
    def search_media(self, query: str = "", media_type: str = "", tags: List[str] = None) -> List[Dict[str, Any]]:
        """Tìm kiếm media"""
        results = self.media_index["files"]
        
        # Filter theo type
        if media_type and media_type != "all":
            results = [m for m in results if m["type"] == media_type]
        
        # Filter theo tags
        if tags:
            results = [
                m for m in results
                if any(tag in m.get("tags", []) for tag in tags)
            ]
        
        # Search theo tên và description
        if query:
            query_lower = query.lower()
            results = [
                m for m in results
                if query_lower in m["original_name"].lower() or
                   query_lower in m.get("description", "").lower()
            ]
        
        # Sắp xếp theo usage và upload time
        return sorted(results, key=lambda x: (x["usage_count"], x["uploaded_at"]), reverse=True)
    
    def use_media(self, media_id: str) -> Dict[str, Any]:
        """Sử dụng media (tăng usage count)"""
        media = self.get_media(media_id)
        if not media:
            return {"success": False, "message": "Không tìm thấy media"}
        
        media["usage_count"] += 1
        media["last_used"] = datetime.now().isoformat()
        self.save_media_index()
        
        return {
            "success": True,
            "path": str(self.get_media_path(media_id)),
            "media_info": media
        }
    
    def delete_media(self, media_id: str) -> Dict[str, Any]:
        """Xóa media"""
        media_index = None
        for i, media_file in enumerate(self.media_index["files"]):
            if media_file["id"] == media_id:
                media_index = i
                break
        
        if media_index is None:
            return {"success": False, "message": "Không tìm thấy media"}
        
        media = self.media_index["files"][media_index]
        
        # Xóa file
        file_path = self.get_media_path(media_id)
        if file_path and file_path.exists():
            file_path.unlink()
        
        # Xóa khỏi index
        self.media_index["files"].pop(media_index)
        
        # Cập nhật tags index
        for tag in media.get("tags", []):
            if tag in self.media_index["tags"]:
                if media_id in self.media_index["tags"][tag]:
                    self.media_index["tags"][tag].remove(media_id)
                if not self.media_index["tags"][tag]:
                    del self.media_index["tags"][tag]
        
        # Cập nhật stats
        self.media_index["stats"]["total_files"] -= 1
        self.media_index["stats"]["total_size"] -= media["size"]
        
        self.save_media_index()
        
        return {
            "success": True,
            "message": f"Đã xóa {media['original_name']} khỏi media library"
        }
    
    def cleanup_unused_media(self, days: int = 30) -> Dict[str, Any]:
        """Dọn dẹp media không sử dụng"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        unused_media = [
            media for media in self.media_index["files"]
            if media["usage_count"] == 0 and media["uploaded_at"] < cutoff_date
        ]
        
        deleted_count = 0
        total_size_freed = 0
        
        for media in unused_media:
            result = self.delete_media(media["id"])
            if result["success"]:
                deleted_count += 1
                total_size_freed += media["size"]
        
        self.media_index["stats"]["last_cleanup"] = datetime.now().isoformat()
        self.save_media_index()
        
        return {
            "deleted_count": deleted_count,
            "size_freed": total_size_freed,
            "message": f"Đã dọn dẹp {deleted_count} file, giải phóng {total_size_freed / 1024 / 1024:.2f}MB"
        }
    
    def get_media_stats(self) -> Dict[str, Any]:
        """Lấy thống kê media library"""
        type_counts = {}
        type_sizes = {}
        
        for media in self.media_index["files"]:
            media_type = media["type"]
            type_counts[media_type] = type_counts.get(media_type, 0) + 1
            type_sizes[media_type] = type_sizes.get(media_type, 0) + media["size"]
        
        return {
            "total_files": len(self.media_index["files"]),
            "total_size": self.media_index["stats"]["total_size"],
            "total_size_mb": self.media_index["stats"]["total_size"] / 1024 / 1024,
            "type_breakdown": {
                "counts": type_counts,
                "sizes": type_sizes
            },
            "top_tags": sorted(
                self.media_index["tags"].items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]
        }
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Tính hash của file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _generate_media_id(self) -> str:
        """Tạo ID duy nhất cho media"""
        return f"media_{int(datetime.now().timestamp())}_{len(self.media_index['files'])}"
    
    # ============ BACKUP & EXPORT ============
    
    def export_templates(self, filename: Optional[str] = None) -> str:
        """Xuất templates ra file"""
        if not filename:
            filename = f"templates_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Đã xuất templates ra {filename}")
            return filename
        except Exception as e:
            logger.error(f"Lỗi khi xuất templates: {e}")
            return ""
    
    def import_templates(self, filename: str) -> Dict[str, Any]:
        """Nhập templates từ file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            imported_count = 0
            for template in imported_data.get("templates", []):
                # Tạo ID mới để tránh conflict
                template["id"] = self._generate_template_id()
                template["imported_at"] = datetime.now().isoformat()
                self.templates["templates"].append(template)
                imported_count += 1
            
            self.save_templates()
            
            return {
                "success": True,
                "imported_count": imported_count,
                "message": f"Đã nhập {imported_count} templates thành công"
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi nhập templates: {e}")
            return {"success": False, "message": f"Lỗi: {str(e)}"}

# Global instance
template_manager = TemplateManager() 