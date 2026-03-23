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

    with gr.Blocks(title=t("app.title")) as app:
        # Inject custom CSS
        gr.HTML(f"<style>{custom_css}</style>", visible=False)

        # Header
        gr.Markdown(f"""
<div class="app-header">
    <h1 class="app-title">{t("app.title")}</h1>
    <p class="app-subtitle">{t("app.subtitle")}</p>
</div>
""")

        with gr.Tabs():
            from ui.create_tab import build_create_tab
            from ui.continue_tab import build_continue_tab
            from ui.projects_tab import build_projects_tab
            from ui.settings_tab import build_settings_tab

            build_create_tab()
            build_continue_tab()
            build_projects_tab()
            build_settings_tab()

        # Footer
        gr.Markdown("""
<div class="app-footer">
    <p>TiniX Story v1.0.0</p>
    <p class="footer-credit">Made with care by TiniX AI</p>
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