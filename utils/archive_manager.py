"""
Mô-đun quản lý kho lưu trữ dự án - Xuất/nhập dự án dạng ZIP
"""
import os
import re
import json
import zipfile
import logging
from typing import Tuple, Optional
from datetime import datetime

from locales.i18n import t

logger = logging.getLogger(__name__)

MODULE_ROOT = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_DIR = os.path.join(MODULE_ROOT, "exports")
try:
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
except OSError:
    ARCHIVE_DIR = os.path.join("/tmp", "exports")
    os.makedirs(ARCHIVE_DIR, exist_ok=True)


def export_project_archive(project_id: str) -> Tuple[Optional[str], str]:
    """
    Xuất dự án thành file ZIP (metadata.json + nội dung các chương)

    Args:
        project_id: ID dự án cần xuất

    Returns:
        (Đường dẫn tệp ZIP, thông tin trạng thái)
    """
    try:
        from core.database import get_db

        conn = get_db()
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            return None, t("archive.project_not_found", id=project_id)

        # Xây dựng metadata
        metadata = {
            "id": row["id"],
            "title": row["title"],
            "genre": row["genre"],
            "sub_genres": row["sub_genres"],
            "character_setting": row["character_setting"],
            "world_setting": row["world_setting"],
            "plot_idea": row["plot_idea"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "export_at": datetime.now().isoformat(),
        }

        # Tải chapters
        ch_rows = conn.execute(
            "SELECT * FROM chapters WHERE project_id = ? ORDER BY num", (project_id,)
        ).fetchall()

        chapters = []
        for ch in ch_rows:
            chapters.append({
                "num": ch["num"],
                "title": ch["title"],
                "desc": ch["desc"],
                "content": ch["content"],
                "word_count": ch["word_count"],
                "generated_at": ch["generated_at"],
            })

        # Tạo file ZIP
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', row["title"])[:80]
        filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tinix.zip"
        filepath = os.path.join(ARCHIVE_DIR, filename)

        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))
            for ch in chapters:
                ch_filename = f"chapters/chapter_{ch['num']:03d}.json"
                zf.writestr(ch_filename, json.dumps(ch, ensure_ascii=False, indent=2))

        logger.info(f"Archive export success: {filename}")
        return filepath, t("archive.export_success", filename=filename, count=len(chapters))

    except Exception as e:
        logger.error(f"Archive export failed: {e}")
        return None, t("archive.export_failed", error=str(e))


def import_project_archive(zip_path: str) -> Tuple[bool, str]:
    """
    Nhập dự án từ file ZIP

    Args:
        zip_path: Đường dẫn file ZIP

    Returns:
        (Thành công, thông tin trạng thái)
    """
    try:
        from services.project_manager import ProjectManager

        if not os.path.exists(zip_path):
            return False, t("archive.file_not_found", path=zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            if "metadata.json" not in zf.namelist():
                return False, t("archive.invalid_archive")

            metadata = json.loads(zf.read("metadata.json").decode('utf-8'))

            # Đọc chapters
            chapter_files = sorted([n for n in zf.namelist() if n.startswith("chapters/") and n.endswith(".json")])
            chapters_data = []
            for ch_file in chapter_files:
                ch = json.loads(zf.read(ch_file).decode('utf-8'))
                chapters_data.append(ch)

        # Tạo dự án
        title = metadata.get("title", "Imported Project")
        genre = metadata.get("genre", "")
        sub_genres_raw = metadata.get("sub_genres", "[]")
        if isinstance(sub_genres_raw, str):
            try:
                sub_genres = json.loads(sub_genres_raw)
            except Exception:
                sub_genres = []
        else:
            sub_genres = sub_genres_raw

        success, msg = ProjectManager.create_project_from_import(
            title=title,
            genre=genre,
            sub_genres=sub_genres,
            character_setting=metadata.get("character_setting", ""),
            world_setting=metadata.get("world_setting", ""),
            plot_idea=metadata.get("plot_idea", ""),
            chapters=chapters_data,
        )

        if success:
            logger.info(f"Archive import success: {title}")
            return True, t("archive.import_success", title=title, count=len(chapters_data))
        return False, msg

    except Exception as e:
        logger.error(f"Archive import failed: {e}")
        return False, t("archive.import_failed", error=str(e))
