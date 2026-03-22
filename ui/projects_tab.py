import gradio as gr
from locales.i18n import t
from services.project_manager import ProjectManager, list_project_titles
from services.consistency_checker import ConsistencyChecker
import logging

logger = logging.getLogger(__name__)


def _build_dashboard_html(stats):
    """Tạo HTML bảng dashboard dự án"""
    if not stats:
        return f"<p style='color:gray'>{t('dashboard.no_projects')}</p>"

    rows_html = ""
    for p in stats:
        total = p.get("total_chapters", 0) or 0
        completed = p.get("completed_chapters", 0) or 0
        words = p.get("total_words", 0) or 0
        pct = int(completed / total * 100) if total > 0 else 0
        updated = (p.get("updated_at") or "")[:10]
        rows_html += f"""
        <tr>
          <td style='padding:6px 10px'>{p.get('title','')}</td>
          <td style='padding:6px 10px'>{p.get('genre','')}</td>
          <td style='padding:6px 10px'>
            <div style='background:#e0e0e0;border-radius:4px;height:12px;width:100px;display:inline-block;vertical-align:middle'>
              <div style='background:#4caf50;height:100%;width:{pct}%;border-radius:4px'></div>
            </div>
            <span style='margin-left:6px;font-size:0.85em'>{completed}/{total} ({pct}%)</span>
          </td>
          <td style='padding:6px 10px'>{words:,}</td>
          <td style='padding:6px 10px'>{updated}</td>
        </tr>"""

    return f"""
    <table style='border-collapse:collapse;width:100%;font-size:0.9em'>
      <thead>
        <tr style='background:#1f2937;color:#f9fafb'>
          <th style='padding:8px 10px;text-align:left'>{t('dashboard.col_title')}</th>
          <th style='padding:8px 10px;text-align:left'>{t('dashboard.col_genre')}</th>
          <th style='padding:8px 10px;text-align:left'>{t('dashboard.col_progress')}</th>
          <th style='padding:8px 10px;text-align:left'>{t('dashboard.col_words')}</th>
          <th style='padding:8px 10px;text-align:left'>{t('dashboard.col_updated')}</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>"""


def build_projects_tab():
    with gr.Tab(t("tabs.projects")):
        gr.Markdown(f"### {t('projects.header')}")

        # === Dashboard Section ===
        with gr.Accordion(f"📊 {t('dashboard.header')}", open=True):
            dashboard_html = gr.HTML(value=_build_dashboard_html([]))
            refresh_dashboard_btn = gr.Button(t("projects.refresh_btn"))

        # === Delete Section ===
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
                stats = ProjectManager.get_project_stats()
                html = _build_dashboard_html(stats)
                titles = [p.get("title", "") for p in stats]
                return html, gr.update(choices=titles, value=None)
            except Exception as e:
                logger.error(f"Refresh projects failed: {e}")
                return _build_dashboard_html([]), gr.update()

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
                    new_html, new_dropdown = on_refresh_projects()
                    return f"✅ {t('projects.delete_success')}", new_html, new_dropdown
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

            with gr.Accordion(t("version.accordion_title"), open=False):
                with gr.Row():
                    version_dropdown = gr.Dropdown(
                        choices=[], label=t("version.dropdown_label"), interactive=True, scale=3
                    )
                    version_view_btn = gr.Button(t("version.view_btn"), scale=1)
                    version_rollback_btn = gr.Button(t("version.rollback_btn"), variant="stop", scale=1)
                version_content = gr.Textbox(
                    label=t("version.view_label"), lines=10, interactive=False
                )
                version_status = gr.Textbox(label=t("version.status_label"), interactive=False)

            # Trạng thái nội bộ lưu project_id
            editor_project_id = gr.State(value=None)
            editor_chapter_num = gr.State(value=None)

            # === Chapter Management Controls ===
            with gr.Accordion(f"🔧 {t('chapter_mgmt.header')}", open=False):
                with gr.Row():
                    move_up_btn = gr.Button(t("chapter_mgmt.move_up"), scale=1)
                    move_down_btn = gr.Button(t("chapter_mgmt.move_down"), scale=1)
                    merge_next_btn = gr.Button(t("chapter_mgmt.merge_next"), variant="secondary", scale=1)
                    delete_chapter_btn = gr.Button(t("chapter_mgmt.delete_chapter"), variant="stop", scale=1)

                gr.Markdown(f"**{t('chapter_mgmt.insert_header')}**")
                with gr.Row():
                    insert_title_input = gr.Textbox(label=t("chapter_mgmt.insert_title"), scale=2, placeholder=t("chapter_mgmt.insert_title_ph"))
                    insert_desc_input = gr.Textbox(label=t("chapter_mgmt.insert_desc"), scale=3, placeholder=t("chapter_mgmt.insert_desc_ph"))
                    insert_btn = gr.Button(t("chapter_mgmt.insert_btn"), variant="primary", scale=1)

                chapter_mgmt_status = gr.Textbox(label=t("chapter_mgmt.status"), interactive=False)

            def on_editor_project_select(project_title):
                if not project_title:
                    return gr.update(choices=[], value=None), "", 0, None, None
                project_data = ProjectManager.get_project_by_title(project_title)
                if not project_data:
                    return gr.update(choices=[], value=None), "", 0, None, None
                project_id = project_data["id"]
                chapters = ProjectManager.get_chapter_list(project_id)
                ch_choices = [f"Ch {c['num']}: {c['title']}" for c in chapters]
                return gr.update(choices=ch_choices, value=None), "", 0, project_id, None

            def on_editor_chapter_select(chapter_label, project_id):
                if not chapter_label or not project_id:
                    return "", 0, None
                try:
                    ch_num = int(chapter_label.split(":")[0].replace("Ch ", "").strip())
                except (ValueError, IndexError):
                    return "", 0, None
                chapters = ProjectManager.get_chapter_list(project_id)
                for c in chapters:
                    if c["num"] == ch_num:
                        content = c["content"] or ""
                        return content, len(content.split()), ch_num
                return "", 0, None

            def on_editor_content_change(content):
                return len(content.split()) if content else 0

            def on_editor_save(chapter_label, content, project_id):
                if not chapter_label or not project_id:
                    return f"❌ {t('projects.select_project_first')}"
                try:
                    ch_num = int(chapter_label.split(":")[0].replace("Ch ", "").strip())
                except (ValueError, IndexError):
                    return "❌ Invalid chapter"
                success, msg = ProjectManager.update_chapter_content(project_id, ch_num, content)
                return f"✅ {t('projects.save_success')}" if success else f"❌ {msg}"

            def _reload_chapters(project_id, current_num=None):
                """Tải lại danh sách chương sau khi thay đổi"""
                if not project_id:
                    return gr.update(choices=[], value=None)
                chapters = ProjectManager.get_chapter_list(project_id)
                ch_choices = [f"Ch {c['num']}: {c['title']}" for c in chapters]
                selected = None
                if current_num is not None:
                    for choice in ch_choices:
                        try:
                            n = int(choice.split(":")[0].replace("Ch ", "").strip())
                            if n == current_num:
                                selected = choice
                                break
                        except Exception:
                            pass
                return gr.update(choices=ch_choices, value=selected)

            def on_move_up(project_id, ch_num):
                if not project_id or not ch_num:
                    return f"❌ {t('projects.select_project_first')}", gr.update()
                if int(ch_num) <= 1:
                    return f"❌ {t('chapter_mgmt.already_first')}", gr.update()
                success, msg = ProjectManager.reorder_chapter(project_id, int(ch_num), int(ch_num) - 1)
                new_num = int(ch_num) - 1 if success else int(ch_num)
                return (f"✅ {msg}" if success else f"❌ {msg}"), _reload_chapters(project_id, new_num)

            def on_move_down(project_id, ch_num):
                if not project_id or not ch_num:
                    return f"❌ {t('projects.select_project_first')}", gr.update()
                chapters = ProjectManager.get_chapter_list(project_id)
                max_num = max((c["num"] for c in chapters), default=0)
                if int(ch_num) >= max_num:
                    return f"❌ {t('chapter_mgmt.already_last')}", gr.update()
                success, msg = ProjectManager.reorder_chapter(project_id, int(ch_num), int(ch_num) + 1)
                new_num = int(ch_num) + 1 if success else int(ch_num)
                return (f"✅ {msg}" if success else f"❌ {msg}"), _reload_chapters(project_id, new_num)

            def on_insert_chapter(project_id, ch_num, title, desc):
                if not project_id or not ch_num:
                    return f"❌ {t('projects.select_project_first')}", gr.update()
                new_num, msg = ProjectManager.insert_chapter(project_id, int(ch_num), title or "", desc or "")
                if new_num > 0:
                    return f"✅ {msg}", _reload_chapters(project_id, new_num)
                return f"❌ {msg}", gr.update()

            def on_delete_chapter(project_id, ch_num):
                if not project_id or not ch_num:
                    return f"❌ {t('projects.select_project_first')}", gr.update()
                success, msg = ProjectManager.delete_chapter(project_id, int(ch_num))
                if success:
                    return f"✅ {msg}", _reload_chapters(project_id, None)
                return f"❌ {msg}", gr.update()

            def on_merge_next(project_id, ch_num):
                if not project_id or not ch_num:
                    return f"❌ {t('projects.select_project_first')}", gr.update()
                chapters = ProjectManager.get_chapter_list(project_id)
                nums = sorted(c["num"] for c in chapters)
                idx = nums.index(int(ch_num)) if int(ch_num) in nums else -1
                if idx < 0 or idx >= len(nums) - 1:
                    return f"❌ {t('chapter_mgmt.no_next_chapter')}", gr.update()
                next_num = nums[idx + 1]
                success, msg = ProjectManager.merge_chapters(project_id, int(ch_num), next_num)
                if success:
                    return f"✅ {msg}", _reload_chapters(project_id, int(ch_num))
                return f"❌ {msg}", gr.update()

            def _parse_chapter_num(chapter_label):
                """Trích số chương từ label 'Ch X: ...'"""
                try:
                    return int(chapter_label.split(":")[0].replace("Ch ", "").strip())
                except (ValueError, IndexError, AttributeError):
                    return None

            def on_version_chapter_select(chapter_label, project_id):
                """Load danh sách phiên bản khi chọn chương."""
                if not chapter_label or not project_id:
                    return gr.update(choices=[], value=None)
                ch_num = _parse_chapter_num(chapter_label)
                if ch_num is None:
                    return gr.update(choices=[], value=None)
                try:
                    from services.version_manager import VersionManager
                    versions = VersionManager.list_versions(project_id, ch_num)
                    if not versions:
                        return gr.update(choices=[], value=None)
                    choices = [
                        t("version.version_entry", version=v["version"], words=v["word_count"],
                          date=v["created_at"][:16] if v["created_at"] else "")
                        for v in versions
                    ]
                    return gr.update(choices=choices, value=choices[0])
                except Exception as e:
                    logger.error(f"Load versions failed: {e}")
                    return gr.update(choices=[], value=None)

            def on_version_view(version_entry, chapter_label, project_id):
                """Hiển thị nội dung phiên bản được chọn."""
                if not version_entry or not chapter_label or not project_id:
                    return "", f"❌ {t('version.no_chapter')}"
                ch_num = _parse_chapter_num(chapter_label)
                if ch_num is None:
                    return "", f"❌ {t('version.no_chapter')}"
                try:
                    # Trích số phiên bản từ entry string "vX — ..."
                    ver_num = int(version_entry.split("—")[0].replace("v", "").strip())
                    from services.version_manager import VersionManager
                    content = VersionManager.get_version(project_id, ch_num, ver_num)
                    if content is None:
                        return "", f"❌ {t('version.no_versions')}"
                    return content, f"✅ Đang xem phiên bản {ver_num}"
                except Exception as e:
                    return "", f"❌ {str(e)}"

            def on_version_rollback(version_entry, chapter_label, project_id):
                """Khôi phục chương về phiên bản được chọn."""
                if not version_entry or not chapter_label or not project_id:
                    return f"❌ {t('version.no_chapter')}", gr.update()
                ch_num = _parse_chapter_num(chapter_label)
                if ch_num is None:
                    return f"❌ {t('version.no_chapter')}", gr.update()
                try:
                    ver_num = int(version_entry.split("—")[0].replace("v", "").strip())
                    from services.version_manager import VersionManager
                    ok = VersionManager.rollback(project_id, ch_num, ver_num)
                    if ok:
                        # Làm mới danh sách phiên bản sau khi khôi phục
                        new_versions = VersionManager.list_versions(project_id, ch_num)
                        choices = [
                            t("version.version_entry", version=v["version"], words=v["word_count"],
                              date=v["created_at"][:16] if v["created_at"] else "")
                            for v in new_versions
                        ]
                        return t("version.rollback_success", version=ver_num), gr.update(choices=choices, value=choices[0] if choices else None)
                    return f"❌ {t('version.rollback_failed')}", gr.update()
                except Exception as e:
                    return f"❌ {str(e)}", gr.update()

            editor_project_selector.change(
                fn=on_editor_project_select,
                inputs=[editor_project_selector],
                outputs=[editor_chapter_selector, editor_textbox, editor_word_count, editor_project_id, editor_chapter_num]
            )
            editor_chapter_selector.change(
                fn=on_editor_chapter_select,
                inputs=[editor_chapter_selector, editor_project_id],
                outputs=[editor_textbox, editor_word_count, editor_chapter_num]
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
            move_up_btn.click(
                fn=on_move_up,
                inputs=[editor_project_id, editor_chapter_num],
                outputs=[chapter_mgmt_status, editor_chapter_selector]
            )
            move_down_btn.click(
                fn=on_move_down,
                inputs=[editor_project_id, editor_chapter_num],
                outputs=[chapter_mgmt_status, editor_chapter_selector]
            )
            insert_btn.click(
                fn=on_insert_chapter,
                inputs=[editor_project_id, editor_chapter_num, insert_title_input, insert_desc_input],
                outputs=[chapter_mgmt_status, editor_chapter_selector]
            )
            delete_chapter_btn.click(
                fn=on_delete_chapter,
                inputs=[editor_project_id, editor_chapter_num],
                outputs=[chapter_mgmt_status, editor_chapter_selector]
            )
            merge_next_btn.click(
                fn=on_merge_next,
                inputs=[editor_project_id, editor_chapter_num],
                outputs=[chapter_mgmt_status, editor_chapter_selector]
            )

        # === Consistency Check Section ===
        with gr.Accordion(f"🔍 {t('consistency.accordion_label')}", open=False):
            consistency_project_selector = gr.Dropdown(
                choices=list_project_titles(),
                label=t("consistency.select_project"),
                interactive=True
            )
            consistency_check_btn = gr.Button(t("consistency.check_btn"), variant="primary")
            consistency_status = gr.Textbox(label=t("projects.status_label"), interactive=False)
            consistency_result = gr.Markdown("")

            consistency_project_id = gr.State(value=None)

            def on_consistency_project_select(project_title):
                if not project_title:
                    return None
                project_data = ProjectManager.get_project_by_title(project_title)
                return project_data["id"] if project_data else None

            def on_check_consistency(project_id):
                if not project_id:
                    return t("consistency.status_no_project"), ""
                try:
                    issues = ConsistencyChecker.check_project(project_id)
                    if issues is None:
                        return t("consistency.status_not_enough"), ""
                    report = ConsistencyChecker.format_report(issues)
                    return t("consistency.status_done"), report
                except Exception as e:
                    logger.error(f"Consistency check failed: {e}")
                    return f"❌ {str(e)}", ""

            consistency_project_selector.change(
                fn=on_consistency_project_select,
                inputs=[consistency_project_selector],
                outputs=[consistency_project_id]
            )
            consistency_check_btn.click(
                fn=on_check_consistency,
                inputs=[consistency_project_id],
                outputs=[consistency_status, consistency_result]
            )

        # === Project Archives Section ===
        with gr.Accordion(f"📦 {t('archive.header')}", open=False):
            gr.Markdown(t("archive.description"))
            with gr.Row():
                archive_project_selector = gr.Dropdown(
                    choices=list_project_titles(),
                    label=t("archive.select_project"),
                    interactive=True, scale=3
                )
                archive_export_btn = gr.Button(t("archive.export_btn"), variant="primary", scale=1)
            archive_export_status = gr.Textbox(label=t("archive.export_status"), interactive=False)
            archive_export_download = gr.File(label=t("archive.download_label"), interactive=False)

            gr.Markdown("---")
            archive_import_file = gr.File(label=t("archive.import_label"), file_types=[".zip"])
            archive_import_btn = gr.Button(t("archive.import_btn"), variant="secondary")
            archive_import_status = gr.Textbox(label=t("archive.import_status"), interactive=False)

            def on_archive_export(project_title):
                if not project_title:
                    return f"❌ {t('projects.select_project_first')}", None
                try:
                    project_data = ProjectManager.get_project_by_title(project_title)
                    if not project_data:
                        return f"❌ {t('projects.project_not_found')}", None
                    from utils.archive_manager import export_project_archive
                    filepath, msg = export_project_archive(project_data["id"])
                    if filepath:
                        return f"✅ {msg}", filepath
                    return f"❌ {msg}", None
                except Exception as e:
                    logger.error(f"Archive export failed: {e}")
                    return f"❌ {str(e)}", None

            def on_archive_import(zip_file):
                if not zip_file:
                    return f"❌ {t('archive.no_file')}"
                try:
                    from utils.archive_manager import import_project_archive
                    file_path = zip_file.name if hasattr(zip_file, 'name') else zip_file
                    success, msg = import_project_archive(file_path)
                    return f"✅ {msg}" if success else f"❌ {msg}"
                except Exception as e:
                    logger.error(f"Archive import failed: {e}")
                    return f"❌ {str(e)}"

            archive_export_btn.click(
                fn=on_archive_export,
                inputs=[archive_project_selector],
                outputs=[archive_export_status, archive_export_download]
            )
            archive_import_btn.click(
                fn=on_archive_import,
                inputs=[archive_import_file],
                outputs=[archive_import_status]
            )

            # Cập nhật danh sách phiên bản khi chọn chương
            editor_chapter_selector.change(
                fn=on_version_chapter_select,
                inputs=[editor_chapter_selector, editor_project_id],
                outputs=[version_dropdown]
            )
            version_view_btn.click(
                fn=on_version_view,
                inputs=[version_dropdown, editor_chapter_selector, editor_project_id],
                outputs=[version_content, version_status]
            )
            version_rollback_btn.click(
                fn=on_version_rollback,
                inputs=[version_dropdown, editor_chapter_selector, editor_project_id],
                outputs=[version_status, version_dropdown]
            )

        refresh_dashboard_btn.click(fn=on_refresh_projects, outputs=[dashboard_html, delete_project_selector])
        delete_project_btn.click(
            fn=on_delete_project,
            inputs=[delete_project_selector],
            outputs=[project_manage_status, dashboard_html, delete_project_selector]
        )
