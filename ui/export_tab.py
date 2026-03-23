import gradio as gr
from locales.i18n import t
from services.project_manager import ProjectManager, list_project_titles
from utils.exporter import export_to_docx, export_to_txt, export_to_markdown, export_to_html, export_to_epub, export_to_pdf
import logging

logger = logging.getLogger(__name__)

def build_export_tab():
    with gr.Tab(t("tabs.export")):
        gr.Markdown(f"### {t('export.header')}")

        export_project_selector = gr.Dropdown(
            choices=[],
            label=t("projects.select_project"),
            interactive=True
        )
        refresh_export_btn = gr.Button(t("projects.refresh_btn"), size="sm")

        export_format = gr.Radio(
            choices=[
                t("create.export_format_word"),
                t("create.export_format_txt"),
                t("create.export_format_md"),
                t("create.export_format_html"),
                t("create.export_format_epub"),
                t("create.export_format_pdf"),
            ],
            value=t("create.export_format_txt"),
            label=t("projects.export_format"),
            interactive=True
        )
        export_btn = gr.Button(t("projects.export_btn"), variant="primary", size="lg")
        export_status = gr.Textbox(label=t("projects.export_status"), interactive=False)
        export_download = gr.File(label=t("projects.download_file"), interactive=False)

        # === EPUB Import Section ===
        with gr.Accordion(f"📥 {t('epub_import.header')}", open=False):
            gr.Markdown(t("epub_import.description"))
            epub_upload = gr.File(label=t("epub_import.upload_label"), file_types=[".epub"])
            epub_genre = gr.Textbox(label=t("epub_import.genre_label"), placeholder=t("epub_import.genre_placeholder"))
            epub_import_btn = gr.Button(t("epub_import.import_btn"), variant="primary")
            epub_preview = gr.Textbox(label=t("epub_import.preview_label"), interactive=False, lines=8)
            epub_import_status = gr.Textbox(label=t("epub_import.status_label"), interactive=False)

        def on_refresh_export():
            titles = list_project_titles()
            return gr.update(choices=titles, value=None)

        def on_export(project_title, format_type):
            if not project_title:
                return f"❌ {t('projects.select_project_first')}", None

            try:
                project_data = ProjectManager.get_project_by_title(project_title)
                if not project_data:
                    return f"❌ {t('projects.project_not_found')}", None

                project_id = project_data.get("id")
                project, msg = ProjectManager.load_project(project_id)
                if not project:
                    return f"❌ {msg}", None

                full_text = f"# {project.title}\n\n"
                for ch in project.chapters:
                    if ch.content:
                        full_text += f"## Chương {ch.num}: {ch.title}\n\n"
                        full_text += ch.content + "\n\n"

                if len(full_text.strip()) < 50:
                    return f"❌ {t('ui.no_content_export')}", None

                # Map format
                format_map = {
                    t("create.export_format_word"): "docx",
                    t("create.export_format_txt"): "txt",
                    t("create.export_format_md"): "md",
                    t("create.export_format_html"): "html",
                    t("create.export_format_epub"): "epub",
                    t("create.export_format_pdf"): "pdf",
                }
                fmt = format_map.get(format_type, "txt")

                if fmt == "docx":
                    filepath, exp_msg = export_to_docx(full_text, project.title)
                elif fmt == "txt":
                    filepath, exp_msg = export_to_txt(full_text, project.title)
                elif fmt == "md":
                    filepath, exp_msg = export_to_markdown(full_text, project.title)
                elif fmt == "html":
                    filepath, exp_msg = export_to_html(full_text, project.title)
                elif fmt == "epub":
                    filepath, exp_msg = export_to_epub(full_text, project.title)
                elif fmt == "pdf":
                    filepath, exp_msg = export_to_pdf(full_text, project.title)
                else:
                    return f"❌ {t('ui.unsupported_format', format=fmt)}", None

                if filepath:
                    return f"✅ {exp_msg}", filepath
                return f"❌ {exp_msg}", None

            except Exception as e:
                logger.error(f"Export failed: {e}", exc_info=True)
                return f"❌ {t('ui.export_failed', error=str(e))}", None

        def on_epub_import(epub_file, genre):
            if not epub_file:
                return "", f"❌ {t('epub_import.no_file')}"

            try:
                from utils.file_parser import parse_epub_structured

                file_path = epub_file.name if hasattr(epub_file, 'name') else epub_file
                chapters, metadata, parse_status = parse_epub_structured(file_path)

                if not chapters:
                    return "", f"❌ {parse_status}"

                # Preview
                title = metadata.get('title', '') or 'Imported Novel'
                author = metadata.get('author', '')
                preview_lines = [
                    f"{t('epub_import.detected_title')}: {title}",
                    f"{t('epub_import.detected_author')}: {author}",
                    f"{t('epub_import.detected_chapters')}: {len(chapters)}",
                    "---"
                ]
                for ch in chapters[:5]:
                    preview_lines.append(f"  Ch {ch.num}: {ch.title} ({len(ch.content)} chars)")
                if len(chapters) > 5:
                    preview_lines.append(f"  ... ({len(chapters) - 5} more)")

                # Import vào DB
                chapters_data = [
                    {"num": ch.num, "title": ch.title, "desc": "", "content": ch.content, "word_count": len(ch.content)}
                    for ch in chapters
                ]
                success, import_msg = ProjectManager.create_project_from_import(
                    title=title,
                    genre=genre or "",
                    sub_genres=[],
                    character_setting="",
                    world_setting="",
                    plot_idea="",
                    chapters=chapters_data
                )

                preview_text = "\n".join(preview_lines)
                if success:
                    return preview_text, f"✅ {import_msg}"
                return preview_text, f"❌ {import_msg}"

            except Exception as e:
                logger.error(f"EPUB import failed: {e}", exc_info=True)
                return "", f"❌ {t('epub_import.import_failed', error=str(e))}"

        refresh_export_btn.click(fn=on_refresh_export, outputs=[export_project_selector])
        export_btn.click(fn=on_export, inputs=[export_project_selector, export_format], outputs=[export_status, export_download])
        epub_import_btn.click(fn=on_epub_import, inputs=[epub_upload, epub_genre], outputs=[epub_preview, epub_import_status])
