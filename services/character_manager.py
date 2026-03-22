"""
Mô-đun quản lý nhân vật (Character Bible) — lưu trữ, truy xuất hồ sơ nhân vật cho từng dự án.
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from core.database import get_db
from locales.i18n import t

logger = logging.getLogger(__name__)

_CHARACTER_FIELDS = ("role", "appearance", "personality", "relationships", "arc_notes", "first_chapter")


class CharacterManager:
    """Quản lý hồ sơ nhân vật theo dự án"""

    @staticmethod
    def add_character(project_id: str, name: str, **fields) -> Tuple[bool, str]:
        """
        Thêm nhân vật mới vào dự án.

        Args:
            project_id: ID dự án
            name: Tên nhân vật
            **fields: role, appearance, personality, relationships, arc_notes, first_chapter

        Returns:
            (thành công, thông báo)
        """
        if not project_id or not name or not name.strip():
            return False, t("character.name_required")
        try:
            conn = get_db()
            now = datetime.now().isoformat()
            conn.execute(
                """INSERT INTO characters
                   (project_id, name, role, appearance, personality,
                    relationships, arc_notes, first_chapter, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    project_id,
                    name.strip(),
                    fields.get("role", ""),
                    fields.get("appearance", ""),
                    fields.get("personality", ""),
                    fields.get("relationships", ""),
                    fields.get("arc_notes", ""),
                    int(fields.get("first_chapter", 1) or 1),
                    now,
                    now,
                ),
            )
            conn.commit()
            logger.info(f"Thêm nhân vật '{name}' vào dự án {project_id}")
            return True, t("character.add_success", name=name)
        except Exception as e:
            logger.error(f"Thêm nhân vật thất bại: {e}")
            return False, t("character.add_failed", error=str(e))

    @staticmethod
    def update_character(project_id: str, name: str, **fields) -> Tuple[bool, str]:
        """
        Cập nhật thông tin nhân vật.

        Returns:
            (thành công, thông báo)
        """
        if not project_id or not name:
            return False, t("character.name_required")
        try:
            conn = get_db()
            now = datetime.now().isoformat()
            # Xây dựng SET clause động từ fields được truyền vào
            allowed = {k: v for k, v in fields.items() if k in _CHARACTER_FIELDS}
            if not allowed:
                return False, t("character.no_fields")
            set_clause = ", ".join(f"{k} = ?" for k in allowed)
            values = list(allowed.values()) + [now, project_id, name.strip()]
            cursor = conn.execute(
                f"UPDATE characters SET {set_clause}, updated_at = ? WHERE project_id = ? AND name = ?",
                values,
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, t("character.not_found", name=name)
            logger.info(f"Cập nhật nhân vật '{name}' dự án {project_id}")
            return True, t("character.update_success", name=name)
        except Exception as e:
            logger.error(f"Cập nhật nhân vật thất bại: {e}")
            return False, t("character.update_failed", error=str(e))

    @staticmethod
    def delete_character(project_id: str, name: str) -> Tuple[bool, str]:
        """
        Xóa nhân vật khỏi dự án.

        Returns:
            (thành công, thông báo)
        """
        if not project_id or not name:
            return False, t("character.name_required")
        try:
            conn = get_db()
            cursor = conn.execute(
                "DELETE FROM characters WHERE project_id = ? AND name = ?",
                (project_id, name.strip()),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, t("character.not_found", name=name)
            logger.info(f"Đã xóa nhân vật '{name}' dự án {project_id}")
            return True, t("character.delete_success", name=name)
        except Exception as e:
            logger.error(f"Xóa nhân vật thất bại: {e}")
            return False, t("character.delete_failed", error=str(e))

    @staticmethod
    def list_characters(project_id: str) -> List[Dict]:
        """
        Lấy danh sách nhân vật của dự án.

        Returns:
            Danh sách dict nhân vật
        """
        if not project_id:
            return []
        try:
            conn = get_db()
            rows = conn.execute(
                """SELECT id, name, role, appearance, personality,
                          relationships, arc_notes, first_chapter, created_at, updated_at
                   FROM characters WHERE project_id = ? ORDER BY first_chapter, name""",
                (project_id,),
            ).fetchall()
            return [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "role": r["role"],
                    "appearance": r["appearance"],
                    "personality": r["personality"],
                    "relationships": r["relationships"],
                    "arc_notes": r["arc_notes"],
                    "first_chapter": r["first_chapter"],
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Liệt kê nhân vật thất bại: {e}")
            return []

    @staticmethod
    def get_character_context(project_id: str) -> str:
        """
        Tạo chuỗi mô tả nhân vật dùng cho prompt tiêm vào khi sinh chương.

        Returns:
            Chuỗi văn bản mô tả nhân vật, hoặc rỗng nếu không có nhân vật.
        """
        chars = CharacterManager.list_characters(project_id)
        if not chars:
            return ""
        lines = []
        for c in chars:
            parts = [f"**{c['name']}**"]
            if c.get("role"):
                parts.append(f"Vai trò: {c['role']}")
            if c.get("appearance"):
                parts.append(f"Ngoại hình: {c['appearance']}")
            if c.get("personality"):
                parts.append(f"Tính cách: {c['personality']}")
            if c.get("relationships"):
                parts.append(f"Quan hệ: {c['relationships']}")
            if c.get("arc_notes"):
                parts.append(f"Cung bậc: {c['arc_notes']}")
            lines.append(" | ".join(parts))
        return "\n".join(lines)
