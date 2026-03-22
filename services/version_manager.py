"""
Quản lý lịch sử phiên bản chương truyện.
Cho phép lưu, xem và khôi phục các phiên bản nội dung chương.
"""
import logging
from datetime import datetime
from typing import List, Optional
from core.database import get_db

logger = logging.getLogger(__name__)


class VersionManager:
    """Quản lý phiên bản nội dung chương"""

    @staticmethod
    def save_version(project_id: str, chapter_num: int, content: str, word_count: int = 0) -> int:
        """Lưu nội dung hiện tại thành phiên bản mới. Trả về số phiên bản."""
        conn = get_db()
        row = conn.execute(
            "SELECT MAX(version) as max_v FROM chapter_versions WHERE project_id = ? AND chapter_num = ?",
            (project_id, chapter_num)
        ).fetchone()
        next_version = (row["max_v"] or 0) + 1 if row else 1
        wc = word_count or (len(content.split()) if content else 0)
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO chapter_versions (project_id, chapter_num, version, content, word_count, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, chapter_num, next_version, content, wc, now)
        )
        conn.commit()
        logger.info(f"Đã lưu phiên bản {next_version} cho chương {chapter_num} của dự án {project_id}")
        return next_version

    @staticmethod
    def list_versions(project_id: str, chapter_num: int) -> List[dict]:
        """Trả về danh sách tất cả phiên bản của một chương (mới nhất trước)."""
        conn = get_db()
        rows = conn.execute(
            "SELECT version, word_count, created_at FROM chapter_versions WHERE project_id = ? AND chapter_num = ? ORDER BY version DESC",
            (project_id, chapter_num)
        ).fetchall()
        return [{"version": r["version"], "word_count": r["word_count"], "created_at": r["created_at"]} for r in rows]

    @staticmethod
    def get_version(project_id: str, chapter_num: int, version: int) -> Optional[str]:
        """Lấy nội dung của một phiên bản cụ thể."""
        conn = get_db()
        row = conn.execute(
            "SELECT content FROM chapter_versions WHERE project_id = ? AND chapter_num = ? AND version = ?",
            (project_id, chapter_num, version)
        ).fetchone()
        return row["content"] if row else None

    @staticmethod
    def rollback(project_id: str, chapter_num: int, version: int) -> bool:
        """
        Khôi phục chương về phiên bản chỉ định.
        Lưu nội dung hiện tại thành phiên bản mới trước khi khôi phục.
        """
        conn = get_db()
        # Lưu phiên bản hiện tại trước khi ghi đè
        current = conn.execute(
            "SELECT content, word_count FROM chapters WHERE project_id = ? AND num = ?",
            (project_id, chapter_num)
        ).fetchone()
        if current and current["content"] and len(current["content"].strip()) > 10:
            VersionManager.save_version(project_id, chapter_num, current["content"], current["word_count"] or 0)

        # Lấy nội dung phiên bản mục tiêu
        target = VersionManager.get_version(project_id, chapter_num, version)
        if not target:
            logger.warning(f"Không tìm thấy phiên bản {version} của chương {chapter_num}")
            return False

        wc = len(target.split())
        conn.execute(
            "UPDATE chapters SET content = ?, word_count = ? WHERE project_id = ? AND num = ?",
            (target, wc, project_id, chapter_num)
        )
        conn.commit()
        logger.info(f"Đã khôi phục chương {chapter_num} về phiên bản {version}")
        return True
