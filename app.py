"""
TiniX Story 1.0 - Ứng dụng chính
Tích hợp hệ thống sinh tiểu thuyết, quản lý dự án, xuất file
"""

import gradio as gr
import logging
import threading
import json
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import os

# Import các module hiện có
from services.api_client import APIClient, get_api_client, reinit_api_client
from core.config import get_config, ConfigManager, Backend, GenerationConfig, API_PROVIDERS
from services.novel_generator import (
    NovelGenerator, NovelProject, Chapter, OutlineParser,
    get_preset_templates, get_generator,
    save_generation_cache, load_generation_cache, clear_generation_cache,
    list_generation_caches, get_cache_size
)
from services.project_manager import ProjectManager
from core.config_api import ConfigAPIManager
from utils.exporter import export_to_docx, export_to_txt, export_to_markdown, export_to_html
from services.genre_manager import GenreManager
from services.sub_genre_manager import SubGenreManager
from utils.file_parser import parse_novel_file
from locales.i18n import t
from core.database import get_db
from core.logger import get_logger

# ==================== Cấu hình Logging ====================

logger = get_logger("app")
logger.info("=" * 60)
logger.info("TiniX Story 1.0 - Hệ thống log đã khởi tạo")
logger.info("=" * 60)

# Cấu hình biến môi trường
WEB_HOST = os.getenv("NOVEL_TOOL_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("NOVEL_TOOL_PORT", os.getenv("PORT", "7860")))
WEB_SHARE = os.getenv("NOVEL_TOOL_SHARE", "false").lower() in ("1", "true", "yes")


from core.state import app_state
from services.project_manager import ProjectManager, list_project_titles


# ==================== Giao diện chính ====================

def create_main_ui():
    """Tạo giao diện chính"""

    # Tải CSS tùy chỉnh
    custom_css = ""
    css_path = Path("custom.css")
    if css_path.exists():
        with open(css_path, 'r', encoding='utf-8') as f:
            custom_css = f.read()

    # Đọc theme preference từ DB, inject JS vào CSS để apply dark mode on load
    theme_js = ""
    try:
        conn = get_db()
        theme_row = conn.execute("SELECT value FROM config WHERE key = 'theme'").fetchone()
        if theme_row and theme_row["value"] == "Dark":
            theme_js = '<script>document.addEventListener("DOMContentLoaded",function(){document.body.classList.add("dark-mode")});</script>'
    except Exception:
        pass

    with gr.Blocks(title=t("app.title")) as app:
        # Inject custom CSS + dark mode JS
        gr.HTML(f"<style>{custom_css}</style>{theme_js}", visible=False)

        # Header
        gr.Markdown(f"""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 20px;">
            <h1 style="color: white; margin: 0; font-size: 2.5em;">🚀 {t("app.title")}</h1>
            <h3 style="color: #f0f0f0; margin: 10px 0 0 0;">{t("app.subtitle")}</h3>
        </div>
        """)

        with gr.Tabs():
            from ui.create_tab import build_create_tab
            from ui.continue_tab import build_continue_tab
            from ui.rewrite_tab import build_rewrite_tab
            from ui.polish_tab import build_polish_tab
            from ui.export_tab import build_export_tab
            from ui.projects_tab import build_projects_tab
            from ui.settings_tab import build_settings_tab

            build_create_tab()
            build_continue_tab()
            build_rewrite_tab()
            build_polish_tab()
            build_export_tab()
            build_projects_tab()
            build_settings_tab()

        # Footer
        gr.Markdown("""
        <div style="text-align: center; padding: 15px; margin-top: 30px; border-top: 1px solid #e0e0e0; color: #666;">
            <p style="margin: 5px 0;">TiniX Story v1.0.0</p>
            <p style="margin: 5px 0; font-size: 0.8em; color: #999;">Made with ❤️ by TiniX AI</p>
        </div>
        """)

    return app


# ==================== Khởi động ứng dụng ====================

# Module-level Gradio instance
_gradio_app = create_main_ui()
_gradio_app.queue(default_concurrency_limit=10)

# ASGI app for Vercel/serverless deployments
from fastapi import FastAPI
app = gr.mount_gradio_app(FastAPI(), _gradio_app, path="/")


def main():
    """Khởi động ứng dụng (local/Docker)"""
    logger.info(t("app.startup_log"))
    logger.info(t("app.gradio_start", port=WEB_PORT))
    _gradio_app.launch(
        server_name=WEB_HOST,
        server_port=WEB_PORT,
        share=WEB_SHARE,
        show_error=True
    )


if __name__ == "__main__":
    main()