"""
Mô-đun phân tích tiểu thuyết bằng AI — phân tích nhân vật, thế giới, cốt truyện, thể loại.
"""
import json
import logging
from typing import List, Dict

from services.api_client import get_api_client
from locales.i18n import t

logger = logging.getLogger(__name__)

_GENRE_DATA_PATH = "data/genres.json"


def _load_genre_names() -> List[str]:
    """Tải danh sách tên thể loại từ file data"""
    try:
        with open(_GENRE_DATA_PATH, "r", encoding="utf-8") as f:
            genres = json.load(f)
        return [g["name"] for g in genres if isinstance(g, dict) and "name" in g]
    except Exception:
        return []


class NovelAnalyzer:
    """Phân tích nội dung tiểu thuyết bằng AI"""

    @staticmethod
    def analyze_novel(text: str) -> Dict:
        """
        Phân tích văn bản tiểu thuyết, trả về {characters, world, plot, genre, style}

        Args:
            text: Nội dung văn bản tiểu thuyết

        Returns:
            Dict với các key: characters, world, plot, genre, style
        """
        if not text or not text.strip():
            return {"error": t("analyzer.empty_text")}

        chunks = NovelAnalyzer._chunk_text(text, max_chars=6000)
        if not chunks:
            return {"error": t("analyzer.empty_text")}

        # Phân tích tối đa 5 chunk đầu để lấy nhân vật/bối cảnh/cốt truyện
        analysis_chunks = chunks[:5]
        analyses = []
        for i, chunk in enumerate(analysis_chunks):
            logger.info(f"Phân tích chunk {i + 1}/{len(analysis_chunks)}...")
            result = NovelAnalyzer._analyze_chunk(chunk)
            if result:
                analyses.append(result)

        if not analyses:
            return {"error": t("analyzer.analysis_failed")}

        # Gộp nhiều kết quả phân tích
        merged = NovelAnalyzer._merge_analyses(analyses)

        # Phát hiện thể loại từ 2 chunk đầu
        genre = NovelAnalyzer._detect_genre(chunks[:2])
        merged["genre"] = genre

        return merged

    @staticmethod
    def _chunk_text(text: str, max_chars: int = 6000) -> List[str]:
        """Chia văn bản thành các đoạn theo ranh giới đoạn văn"""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

        chunks = []
        current = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para)
            if current_len + para_len > max_chars and current:
                chunks.append("\n\n".join(current))
                current = [para]
                current_len = para_len
            else:
                current.append(para)
                current_len += para_len

        if current:
            chunks.append("\n\n".join(current))

        return chunks

    @staticmethod
    def _analyze_chunk(chunk: str) -> Dict:
        """Dùng AI để trích xuất nhân vật, bối cảnh, cốt truyện từ một đoạn"""
        api_client = get_api_client()
        prompt = t("analyzer.chunk_prompt", chunk=chunk[:5000])
        messages = [
            {"role": "system", "content": t("analyzer.chunk_system")},
            {"role": "user", "content": prompt},
        ]
        success, content = api_client.generate(messages, use_cache=True)
        if not success:
            logger.warning(f"Phân tích chunk thất bại: {content[:100]}")
            return {}

        try:
            # Thử parse JSON từ response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: trả về text thô trong key "raw"
        return {"raw": content}

    @staticmethod
    def _merge_analyses(analyses: List[Dict]) -> Dict:
        """Dùng AI để gộp nhiều kết quả phân tích thành hồ sơ thống nhất"""
        if len(analyses) == 1:
            result = analyses[0]
            result.pop("raw", None)
            return result

        api_client = get_api_client()
        analyses_text = json.dumps(analyses, ensure_ascii=False, indent=2)
        prompt = t("analyzer.merge_prompt", analyses=analyses_text[:8000])
        messages = [
            {"role": "system", "content": t("analyzer.merge_system")},
            {"role": "user", "content": prompt},
        ]
        success, content = api_client.generate(messages, use_cache=True)
        if not success:
            logger.warning("Gộp phân tích thất bại, dùng kết quả đầu tiên")
            return analyses[0]

        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except (json.JSONDecodeError, ValueError):
            pass

        return {"characters": content, "world": "", "plot": "", "style": ""}

    @staticmethod
    def _detect_genre(chunks: List[str]) -> str:
        """Xác định thể loại từ văn bản, so khớp với danh sách thể loại có sẵn"""
        genre_names = _load_genre_names()
        sample_text = "\n\n".join(chunks)[:4000]
        genre_list_str = ", ".join(genre_names[:30]) if genre_names else ""

        api_client = get_api_client()
        prompt = t("analyzer.genre_prompt", text=sample_text, genres=genre_list_str)
        messages = [
            {"role": "system", "content": t("analyzer.genre_system")},
            {"role": "user", "content": prompt},
        ]
        success, content = api_client.generate(messages, use_cache=True)
        if not success:
            return ""

        # Tìm khớp với danh sách thể loại
        content_lower = content.lower()
        for g in genre_names:
            if g.lower() in content_lower:
                return g

        return content.strip()[:100]
