import gradio as gr
from locales.i18n import t
from services.project_manager import ProjectManager, list_project_titles
import logging

logger = logging.getLogger(__name__)

def build_projects_tab():
    with gr.Tab(t("tabs.projects")):
        gr.Markdown(f"### {t('projects.header')}")

        projects_table = gr.Dataframe(
            headers=["ID", t("ui.col_project_name"), t("ui.col_type"), t("ui.col_created_at"), t("ui.col_chapters")],
            interactive=False
        )
        refresh_projects_btn = gr.Button(t("projects.refresh_btn"))

        gr.Markdown(f"#### {t('projects.delete_header')}")
        delete_project_selector = gr.Dropdown(
            choices=list_project_titles(),
            label=t("projects.delete_select_project"),
            interactive=True
        )
        delete_project_btn = gr.Button(t("projects.delete_btn"), variant="stop")
        project_manage_status = gr.Textbox(label=t("projects.status_label"), interactive=False)

        def on_refresh_projects():
            try:
                projects = ProjectManager.list_projects()
                table_data = []
                for p in projects:
                    table_data.append([
                        p.get("id", ""),
                        p.get("title", ""),
                        p.get("genre", ""),
                        p.get("created_at", "")[:10] if p.get("created_at") else "",
                        f"{p.get('completed_chapters', 0)}/{p.get('chapter_count', 0)}"
                    ])
                titles = [p.get("title", "") for p in projects]
                return table_data, gr.update(choices=titles, value=None)
            except Exception as e:
                logger.error(f"Refresh projects failed: {e}")
                return [], gr.update()

        def on_delete_project(project_title):
            if not project_title or not project_title.strip():
                return f"❌ {t('projects.select_project_first')}", gr.update(), gr.update()

            try:
                project_data = ProjectManager.get_project_by_title(project_title)
                if not project_data:
                    return f"❌ {t('projects.project_not_found')}", gr.update(), gr.update()

                project_id = project_data.get("id")
                success, msg = ProjectManager.delete_project(project_id)
                if success:
                    new_table, new_dropdown = on_refresh_projects()
                    return f"✅ {t('projects.delete_success')}", new_table, new_dropdown
                return f"❌ {t('projects.delete_failed')}: {msg}", gr.update(), gr.update()
            except Exception as e:
                return f"❌ {str(e)}", gr.update(), gr.update()

        # === Chapter Editor Section ===
        with gr.Accordion(f"✏️ {t('projects.editor_header')}", open=False):
            with gr.Row():
                editor_project_selector = gr.Dropdown(
                    choices=list_project_titles(),
                    label=t("projects.select_project"),
                    interactive=True, scale=2
                )
                editor_chapter_selector = gr.Dropdown(
                    choices=[], label=t("projects.editor_select_chapter"),
                    interactive=True, scale=2
                )
            editor_textbox = gr.Textbox(
                label=t("projects.editor_content"),
                interactive=True, lines=20, max_lines=40
            )
            with gr.Row():
                editor_word_count = gr.Number(label=t("projects.word_count"), value=0, interactive=False, scale=1)
                editor_save_btn = gr.Button(t("projects.save_chapter"), variant="primary", scale=1)
            editor_status = gr.Textbox(label=t("projects.status_label"), interactive=False)

            # Trạng thái nội bộ lưu project_id
            editor_project_id = gr.State(value=None)

            def on_editor_project_select(project_title):
                if not project_title:
                    return gr.update(choices=[], value=None), "", 0, None
                project_data = ProjectManager.get_project_by_title(project_title)
                if not project_data:
                    return gr.update(choices=[], value=None), "", 0, None
                project_id = project_data["id"]
                chapters = ProjectManager.get_chapter_list(project_id)
                ch_choices = [f"Ch {c['num']}: {c['title']}" for c in chapters]
                return gr.update(choices=ch_choices, value=None), "", 0, project_id

            def on_editor_chapter_select(chapter_label, project_id):
                if not chapter_label or not project_id:
                    return "", 0
                try:
                    ch_num = int(chapter_label.split(":")[0].replace("Ch ", "").strip())
                except (ValueError, IndexError):
                    return "", 0
                chapters = ProjectManager.get_chapter_list(project_id)
                for c in chapters:
                    if c["num"] == ch_num:
                        content = c["content"] or ""
                        return content, len(content)
                return "", 0

            def on_editor_content_change(content):
                return len(content) if content else 0

            def on_editor_save(chapter_label, content, project_id):
                if not chapter_label or not project_id:
                    return f"❌ {t('projects.select_project_first')}"
                try:
                    ch_num = int(chapter_label.split(":")[0].replace("Ch ", "").strip())
                except (ValueError, IndexError):
                    return "❌ Invalid chapter"
                success, msg = ProjectManager.update_chapter_content(project_id, ch_num, content)
                return f"✅ {t('projects.save_success')}" if success else f"❌ {msg}"

            editor_project_selector.change(
                fn=on_editor_project_select,
                inputs=[editor_project_selector],
                outputs=[editor_chapter_selector, editor_textbox, editor_word_count, editor_project_id]
            )
            editor_chapter_selector.change(
                fn=on_editor_chapter_select,
                inputs=[editor_chapter_selector, editor_project_id],
                outputs=[editor_textbox, editor_word_count]
            )
            editor_textbox.change(
                fn=on_editor_content_change,
                inputs=[editor_textbox],
                outputs=[editor_word_count]
            )
            editor_save_btn.click(
                fn=on_editor_save,
                inputs=[editor_chapter_selector, editor_textbox, editor_project_id],
                outputs=[editor_status]
            )

        refresh_projects_btn.click(fn=on_refresh_projects, outputs=[projects_table, delete_project_selector])
        delete_project_btn.click(
            fn=on_delete_project,
            inputs=[delete_project_selector],
            outputs=[project_manage_status, projects_table, delete_project_selector]
        )
