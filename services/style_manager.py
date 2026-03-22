import os
import json
import logging
from typing import Dict, List, Optional
from locales.i18n import t
from services.api_client import get_api_client

logger = logging.getLogger(__name__)

STYLES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "writing_styles.json")

class StyleManager:
    """Quản lý các phong cách viết truyện và mô tả"""
    
    _cached_styles = None
    _cached_mtime = 0
    
    @classmethod
    def get_default_styles(cls) -> List[Dict[str, str]]:
        """Lấy danh sách phong cách viết mặc định nếu chưa có file"""
        return [
            {
                "name": "Mượt mà tự nhiên, cốt truyện chặt chẽ, nhân vật tinh tế",
                "description": "Văn phong trơn tru, dễ đọc, mạch truyện logic xuyên suốt không có sạn. Xây dựng tâm lý và hành động nhân vật sâu sắc, nhất quán."
            },
            {
                "name": "Văn phong đẹp, ý cảnh sâu xa",
                "description": "Sử dụng từ ngữ trau chuốt, giàu hình ảnh và các phép tu từ. Tập trung miêu tả cảnh vật, nội tâm nhân vật để tạo ra một không gian nghệ thuật đầy cảm xúc."
            },
            {
                "name": "Nhịp nhanh, cốt truyện kịch tính",
                "description": "Tập trung vào hành động, xung đột và diễn biến câu chuyện. Cắt giảm tối đa miêu tả thừa thãi, đưa người đọc đi từ bất ngờ này đến bất ngờ khác."
            },
            {
                "name": "Mô tả tinh tế, cảm xúc phong phú",
                "description": "Chú trọng vào việc thể hiện cảm xúc, rung động tinh vi của nhân vật. Các chi tiết nhỏ trong bối cảnh và tương tác được dùng để tô đậm không khí truyện."
            },
            {
                "name": "Hài hước thú vị, nhẹ nhàng vui vẻ",
                "description": "Sử dụng ngôn ngữ hóm hỉnh, tình huống hài hước dở khóc dở cười. Xoay quanh những mẩu chuyện đời thường hoặc hành trình nhẹ nhàng mang tính giải trí cao."
            }
        ]

    @classmethod
    def ensure_data_dir(cls):
        """Đảm bảo thư mục data tồn tại"""
        os.makedirs(os.path.dirname(STYLES_FILE), exist_ok=True)

    @classmethod
    def load_styles(cls) -> List[Dict[str, str]]:
        """Tải danh sách phong cách từ file (có cache theo mtime)"""
        cls.ensure_data_dir()
        if not os.path.exists(STYLES_FILE):
            default_styles = cls.get_default_styles()
            cls.save_styles(default_styles)
            return default_styles
            
        try:
            current_mtime = os.path.getmtime(STYLES_FILE)
            if cls._cached_styles is not None and cls._cached_mtime == current_mtime:
                return cls._cached_styles
            
            with open(STYLES_FILE, 'r', encoding='utf-8') as f:
                styles = json.load(f)
            cls._cached_styles = styles
            cls._cached_mtime = current_mtime
            return styles
        except Exception as e:
            logger.error(f"Error loading styles: {e}")
            return cls.get_default_styles()

    @classmethod
    def save_styles(cls, styles: List[Dict[str, str]]) -> bool:
        """Lưu danh sách phong cách xuống file"""
        cls.ensure_data_dir()
        try:
            with open(STYLES_FILE, 'w', encoding='utf-8') as f:
                json.dump(styles, f, ensure_ascii=False, indent=4)
            # Invalidate cache
            cls._cached_styles = styles
            cls._cached_mtime = os.path.getmtime(STYLES_FILE)
            return True
        except Exception as e:
            logger.error(f"Error saving styles: {e}")
            return False

    @classmethod
    def add_style(cls, name: str, description: str = "") -> bool:
        """Thêm một phong cách mới"""
        styles = cls.load_styles()
        # Kiểm tra trùng tên
        if any(g["name"] == name for g in styles):
            return False
            
        styles.append({"name": name, "description": description})
        return cls.save_styles(styles)

    @classmethod
    def update_style(cls, old_name: str, new_name: str, description: str) -> bool:
        """Cập nhật thông tin phong cách"""
        styles = cls.load_styles()
        for i, g in enumerate(styles):
            if g["name"] == old_name:
                # Nếu đổi tên, kiểm tra trùng tên mới
                if old_name != new_name and any(x["name"] == new_name for x in styles):
                    return False
                
                styles[i] = {"name": new_name, "description": description}
                return cls.save_styles(styles)
        return False

    @classmethod
    def delete_style(cls, name: str) -> bool:
        """Xóa phong cách"""
        styles = cls.load_styles()
        initial_length = len(styles)
        styles = [g for g in styles if g["name"] != name]
        
        if len(styles) < initial_length:
            return cls.save_styles(styles)
        return False

    @classmethod
    def analyze_style(cls, text: str) -> Dict[str, str]:
        """Phân tích phong cách viết từ đoạn văn bản mẫu bằng AI"""
        if not text or not text.strip():
            return {"error": "Text is empty"}
        try:
            api_client = get_api_client()
            prompt = (
                "Analyze the following text and describe the writing style. "
                "Output ONLY a valid JSON object with exactly two keys:\n"
                '- "name": a short style name (max 50 chars)\n'
                '- "description": detailed style description covering tone, vocabulary, sentence structure, pacing, emotional register\n\n'
                f"Text to analyze:\n{text[:5000]}"
            )
            messages = [
                {"role": "system", "content": "You are a literary style analyst. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ]
            success, response = api_client.generate(messages, use_cache=False)
            if not success or not response:
                return {"error": response or "AI generation failed"}

            # Trích xuất JSON từ response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            result = json.loads(response)
            if "name" in result and "description" in result:
                return result
            return {"error": "Invalid AI response format"}
        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response as JSON"}
        except Exception as e:
            logger.error(f"Analyze style failed: {e}")
            return {"error": str(e)}

    @classmethod
    def get_style_names(cls) -> List[str]:
        """Lấy danh sách tên phong cách để hiển thị UI"""
        styles = cls.load_styles()
        return [g["name"] for g in styles]
        
    @classmethod
    def get_style_description(cls, name: str) -> str:
        """Lấy mô tả hướng dẫn của một phong cách"""
        styles = cls.load_styles()
        for g in styles:
            if g["name"] == name:
                return g["description"]
        return ""
