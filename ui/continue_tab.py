import gradio as gr
from datetime import datetime
from locales.i18n import t
from services.project_manager import ProjectManager, list_project_titles
from services.novel_generator import Chapter, batch_generate_summaries, detect_gaps, fill_all_gaps
from services.novel_analyzer import NovelAnalyzer
from services.character_manager import CharacterManager
from services.style_manager import StyleManager
from core.state import app_state
from utils.file_parser import parse_novel_file
import logging

logger = logging.getLogger(__name__)

def build_continue_tab():
    with gr.Tab(t("tabs.continue_tab")):
        gr.Markdown(f"### {t('continue_tab.header')}")

        with gr.Accordion("📂 1. Quản lý dự án", open=True):
            with gr.Row():
                with gr.Column(scale=4):
                    project_choices = list_project_titles()
                    continue_project_selector = gr.Dropdown(
                        choices=project_choices,
                        label=t("continue_tab.select_project"),
                        interactive=True
                    )
                with gr.Column(scale=1, min_width=100):
                    refresh_continue_btn = gr.Button(t("continue_tab.load_btn"), size="lg")

        with gr.Accordion(f"📝 {t('continue_tab.batch_summary_header')}", open=False):
            with gr.Row():
                batch_summary_btn = gr.Button(t("continue_tab.batch_summary_btn"), variant="secondary", scale=1)
            batch_summary_progress = gr.Textbox(label=t("continue_tab.summary_progress"), interactive=False, lines=8)

        with gr.Accordion("⚙️ 2. Thông tin & Cài đặt", open=False):
            with gr.Row():
                with gr.Column(scale=1):
                    continue_project_info = gr.Markdown(t("continue_tab.no_project_loaded"))
                with gr.Column(scale=2):
                    continue_outline_display = gr.Textbox(
                        label=t("continue_tab.outline_label"),
                        interactive=False, lines=6, max_lines=12,
                        value="Chưa tải dự án..."
                    )

            with gr.Row():
                with gr.Column(scale=1):
                    memory_type = gr.Radio(label="Cách nhớ ngữ cảnh", choices=["Toàn văn", "Tóm tắt"], value="Toàn văn")
                with gr.Column(scale=1):
                    memory_chapters = gr.Number(label="Số chương ghi nhớ", value=3, minimum=1, maximum=20, step=1)
                with gr.Column(scale=1):
                    use_reflection_checkbox = gr.Checkbox(label="Bật chế độ Tự kiểm duyệt (Self-Reflection)", value=False, info="AI tự đọc lại và sửa lỗi nháp. Tốn gấp đôi thời gian & Token.")

            with gr.Row():
                continue_target_words = gr.Number(label=t("rewrite.target_words"), value=3000, minimum=100, maximum=50000, step=100)
                
                style_choices = StyleManager.get_style_names()
                continue_style_dropdown = gr.Dropdown(
                    choices=style_choices,
                    label="Phong cách viết",
                    value=style_choices[0] if style_choices else None,
                    interactive=True
                )
                
                continue_custom_prompt = gr.Textbox(label=t("create.custom_prompt_label"), placeholder=t("create.custom_prompt_placeholder"), scale=2)

        with gr.Accordion(t("analyzer.header"), open=False):
            with gr.Row():
                analyzer_file = gr.File(label=t("analyzer.upload_label"), file_types=[".txt", ".pdf", ".epub", ".md", ".docx"])
                with gr.Column():
                    analyze_btn = gr.Button(t("analyzer.analyze_btn"), variant="secondary")
                    analyze_status = gr.Textbox(label="Status", interactive=False, lines=1)
            analyzer_result = gr.Markdown(label=t("analyzer.result_label"), value="")

        with gr.Accordion(t("gap_filler.header"), open=False):
            with gr.Row():
                detect_gaps_btn = gr.Button(t("gap_filler.detect_btn"), variant="secondary", scale=1)
                fill_all_btn = gr.Button(t("gap_filler.fill_all_btn"), variant="primary", scale=1)
            gaps_display = gr.Textbox(label=t("gap_filler.gaps_label"), interactive=False, lines=5)
            fill_progress = gr.Textbox(label=t("gap_filler.progress_label"), interactive=False, lines=6)

        with gr.Accordion(t("character.header"), open=False):
            char_table = gr.Dataframe(
                headers=["name", "role"],
                label=t("character.table_label"),
                interactive=False,
                row_count=(5, "dynamic"),
            )
            gr.Markdown(f"#### {t('character.add_header')}")
            with gr.Row():
                char_name = gr.Textbox(label=t("character.name_label"), scale=2)
                char_role = gr.Textbox(label=t("character.role_label"), scale=2)
                char_first_ch = gr.Number(label=t("character.first_chapter_label"), value=1, minimum=1, step=1, scale=1)
            char_appearance = gr.Textbox(label=t("character.appearance_label"), lines=2)
            char_personality = gr.Textbox(label=t("character.personality_label"), lines=2)
            char_relationships = gr.Textbox(label=t("character.relationships_label"), lines=2)
            char_arc_notes = gr.Textbox(label=t("character.arc_notes_label"), lines=2)
            with gr.Row():
                char_save_btn = gr.Button(t("character.save_btn"), variant="primary", scale=1)
                char_delete_btn = gr.Button(t("character.delete_btn"), variant="stop", scale=1)
            char_status = gr.Textbox(label=t("character.status_label"), interactive=False, lines=1)

        with gr.Accordion("🚀 3. Sáng tác tiếp", open=False):
            with gr.Row():
                continue_chapter_num = gr.Number(label="Chương số", value=1, minimum=1, scale=1)
                continue_chapter_title = gr.Textbox(label="Tiêu đề chương", placeholder="Nhập tiêu đề chương...", scale=2)
            continue_chapter_desc = gr.Textbox(
                label="Nội dung/Dàn ý chương này",
                lines=3, placeholder="Nhập mô tả nội dung chương..."
            )
            with gr.Row():
                continue_generate_btn = gr.Button(t("continue_tab.continue_gen_btn"), variant="primary", size="lg", scale=1)
                continue_auto_btn = gr.Button("Tự động viết nốt các chương còn lại", variant="primary", size="lg", scale=2)
                continue_stop_btn = gr.Button("Dừng tự động", variant="stop", size="lg", scale=1)
            
            with gr.Row():
                with gr.Column(scale=1):
                    continue_status = gr.Textbox(label=t("continue_tab.gen_status"), interactive=False, lines=15)
                with gr.Column(scale=2):
                    continue_chapter_selector = gr.Dropdown(label="Danh sách chương đã tạo", choices=[], interactive=True, allow_custom_value=True)
                    continue_content_display = gr.Textbox(label="Nội dung chương", lines=15, interactive=False)

        # ── Trình xử lý: Phân tích tiểu thuyết ──
        def on_analyze_novel(file_obj):
            if file_obj is None:
                return t("analyzer.empty_text"), ""
            yield t("analyzer.analyzing"), ""
            try:
                paragraphs, _ = parse_novel_file(file_obj.name)
                text = "\n\n".join(paragraphs)
                result = NovelAnalyzer.analyze_novel(text)
                if "error" in result:
                    yield result["error"], ""
                    return
                md = ""
                if result.get("genre"):
                    md += f"**Thể loại:** {result['genre']}\n\n"
                if result.get("characters"):
                    md += f"**Nhân vật:**\n{result['characters']}\n\n"
                if result.get("world"):
                    md += f"**Thế giới / Bối cảnh:**\n{result['world']}\n\n"
                if result.get("plot"):
                    md += f"**Cốt truyện:**\n{result['plot']}\n\n"
                if result.get("style"):
                    md += f"**Phong cách viết:**\n{result['style']}\n\n"
                yield t("analyzer.done"), md or str(result)
            except Exception as e:
                yield f"❌ {e}", ""

        # ── Trình xử lý: Phát hiện & lấp đầy khoảng trống ──
        def on_detect_gaps(project_title):
            if not project_title:
                return t("gap_filler.no_gaps")
            project_data = ProjectManager.get_project_by_title(project_title)
            if not project_data:
                return t("gap_filler.no_gaps")
            gaps = detect_gaps(project_data["id"])
            if not gaps:
                return t("gap_filler.no_gaps")
            lines = [t("gap_filler.found_gaps", count=len(gaps))]
            for g in gaps:
                lines.append(f"  Chương {g['num']}: {g['title']} ({g['word_count']} ký tự)")
            return "\n".join(lines)

        def on_fill_all_gaps(project_title):
            if not project_title:
                yield t("gap_filler.no_gaps")
                return
            project_data = ProjectManager.get_project_by_title(project_title)
            if not project_data:
                yield t("gap_filler.no_gaps")
                return
            p = project_data
            results = []
            for msg in fill_all_gaps(
                project_id=p["id"],
                novel_title=p.get("title", ""),
                character_setting=p.get("character_setting", ""),
                world_setting=p.get("world_setting", ""),
                plot_idea=p.get("plot_idea", ""),
                genre=p.get("genre", ""),
            ):
                results.append(msg)
                yield "\n".join(results)

        # ── Trình xử lý: Hồ sơ nhân vật ──
        def _get_project_id(project_title):
            if not project_title:
                return None
            pd = ProjectManager.get_project_by_title(project_title)
            return pd["id"] if pd else None

        def on_load_characters(project_title):
            pid = _get_project_id(project_title)
            if not pid:
                return []
            chars = CharacterManager.list_characters(pid)
            return [[c["name"], c["role"]] for c in chars]

        def on_save_character(project_title, name, role, appearance, personality, relationships, arc_notes, first_chapter):
            pid = _get_project_id(project_title)
            if not pid:
                return t("character.no_project"), []
            ok, msg = CharacterManager.add_character(
                pid, name,
                role=role, appearance=appearance, personality=personality,
                relationships=relationships, arc_notes=arc_notes, first_chapter=first_chapter,
            )
            if not ok:
                # Thử update nếu đã tồn tại
                ok, msg = CharacterManager.update_character(
                    pid, name,
                    role=role, appearance=appearance, personality=personality,
                    relationships=relationships, arc_notes=arc_notes, first_chapter=first_chapter,
                )
            chars = CharacterManager.list_characters(pid)
            return msg, [[c["name"], c["role"]] for c in chars]

        def on_delete_character(project_title, name):
            pid = _get_project_id(project_title)
            if not pid:
                return t("character.no_project"), []
            _, msg = CharacterManager.delete_character(pid, name)
            chars = CharacterManager.list_characters(pid)
            return msg, [[c["name"], c["role"]] for c in chars]
        with gr.Accordion(t("multi_model.accordion_title"), open=False):
            mm_enable = gr.Checkbox(label=t("multi_model.enable_label"), value=False)
            from core.config import get_config as _get_config
            _backend_names = [b.name for b in _get_config().get_enabled_backends()]
            mm_backends = gr.CheckboxGroup(
                choices=_backend_names,
                label=t("multi_model.backends_label"),
                value=_backend_names[:2] if len(_backend_names) >= 2 else _backend_names
            )
            mm_compare_btn = gr.Button(t("multi_model.compare_btn"), variant="secondary")
            with gr.Row():
                mm_result_1 = gr.Textbox(label="—", lines=12, interactive=False, scale=1)
                mm_result_2 = gr.Textbox(label="—", lines=12, interactive=False, scale=1)
                mm_result_3 = gr.Textbox(label="—", lines=12, interactive=False, scale=1)
            mm_select = gr.Radio(choices=[], label=t("multi_model.select_best_label"))
            mm_save_btn = gr.Button(t("multi_model.save_btn"), variant="primary")
            mm_status = gr.Textbox(label="", interactive=False)

        def on_mm_compare(project_title, ch_num, ch_title, ch_desc, custom_prompt,
                          mem_type, mem_chaps, selected_style, enabled, selected_backends):
            if not enabled:
                return "—", "—", "—", gr.update(choices=[]), "ℹ️ Bật chế độ so sánh trước"
            if not app_state.current_project:
                return "—", "—", "—", gr.update(choices=[]), f"❌ {t('multi_model.no_project')}"
            if not selected_backends:
                return "—", "—", "—", gr.update(choices=[]), f"❌ {t('multi_model.no_backends')}"

            gen = app_state.get_generator()
            if selected_style:
                gen.config.generation.writing_style = selected_style
            project = app_state.current_project

            all_past = [ch for ch in project.chapters if ch.num < int(ch_num) and getattr(ch, 'content', None)]
            mem_ch = int(mem_chaps) if mem_chaps else 3
            past_chapters = all_past[-mem_ch:] if len(all_past) > mem_ch else all_past
            prev_content = "\n\n".join(c.content for c in past_chapters)[-4000:] if mem_type == "Toàn văn" else (all_past[-1].content[-1500:] if all_past else "")

            results = gen.generate_chapter_multi(
                backend_names=selected_backends,
                chapter_num=int(ch_num), chapter_title=ch_title,
                chapter_desc=ch_desc, novel_title=project.title,
                character_setting=project.character_setting,
                world_setting=project.world_setting,
                plot_idea=project.plot_idea, genre=project.genre,
                sub_genres=project.sub_genres,
                previous_content=prev_content, context_summary="",
                custom_prompt=custom_prompt
            )

            names = list(results.keys())
            vals = [results.get(names[i], "") if i < len(names) else "" for i in range(3)]
            labels = [t("multi_model.result_label", name=names[i]) if i < len(names) else "—" for i in range(3)]
            # Trả về content + cập nhật label
            radio_choices = [names[i] for i in range(min(3, len(names)))]
            return (
                gr.update(value=vals[0], label=labels[0]),
                gr.update(value=vals[1], label=labels[1]),
                gr.update(value=vals[2], label=labels[2]),
                gr.update(choices=radio_choices, value=radio_choices[0] if radio_choices else None),
                t("multi_model.done")
            )

        def on_mm_save(selected_backend, mm_r1, mm_r2, mm_r3, ch_num, ch_title, ch_desc):
            if not selected_backend:
                return f"❌ {t('multi_model.save_no_select')}"
            if not app_state.current_project:
                return f"❌ {t('multi_model.save_no_project')}"
            # Tìm content từ backend được chọn theo thứ tự
            content = ""
            for val in [mm_r1, mm_r2, mm_r3]:
                if val and not val.startswith("❌"):
                    # Kiểm tra nếu đây là kết quả của backend đã chọn (không có cách khác ngoài so sánh)
                    content = val
                    break
            if not content:
                return f"❌ {t('multi_model.save_no_select')}"

            project = app_state.current_project
            from datetime import datetime as _dt
            from services.novel_generator import Chapter as _Chapter
            new_ch = _Chapter(
                num=int(ch_num), title=ch_title, desc=ch_desc,
                content=content, word_count=len(content),
                generated_at=_dt.now().isoformat()
            )
            found = False
            for i, ch in enumerate(project.chapters):
                if ch.num == int(ch_num):
                    project.chapters[i] = new_ch
                    found = True
                    break
            if not found:
                project.chapters.append(new_ch)
                project.chapters.sort(key=lambda x: x.num)
            from services.project_manager import ProjectManager as _PM
            _PM.save_project(project)
            return f"✅ {t('multi_model.save_success', name=selected_backend)}"

        mm_compare_btn.click(
            fn=on_mm_compare,
            inputs=[continue_project_selector, continue_chapter_num, continue_chapter_title,
                    continue_chapter_desc, continue_custom_prompt, memory_type, memory_chapters,
                    continue_style_dropdown, mm_enable, mm_backends],
            outputs=[mm_result_1, mm_result_2, mm_result_3, mm_select, mm_status]
        )
        mm_save_btn.click(
            fn=on_mm_save,
            inputs=[mm_select, mm_result_1, mm_result_2, mm_result_3,
                    continue_chapter_num, continue_chapter_title, continue_chapter_desc],
            outputs=[mm_status]
        )

        def on_refresh_continue(current_title):
            titles = list_project_titles()
            if current_title in titles:
                info, next_ch, outline_text, chapter_choices = on_continue_project_select(current_title)
                return gr.update(choices=titles, value=current_title), info, next_ch, outline_text, gr.update(choices=chapter_choices, value=chapter_choices[-1] if chapter_choices else None)
            else:
                return gr.update(choices=titles, value=None), t("continue_tab.no_project_loaded"), 1, "Chưa tải dự án...", gr.update(choices=[], value=None)

        def on_continue_project_select(project_title):
            if not project_title:
                return t("continue_tab.no_project_loaded"), 1, "Chưa tải dự án...", []
            try:
                project_data = ProjectManager.get_project_by_title(project_title)
                if not project_data:
                    return f"❌ {t('continue_tab.project_not_found')}", 1, "Chưa tải dự án...", []

                project_id = project_data.get("id")
                project, msg = ProjectManager.load_project(project_id)
                if project:
                    app_state.current_project = project
                    completed = project.get_completed_count()
                    total_chapters = len(project.chapters)
                    next_ch = completed + 1
                    percent = f"{(completed / total_chapters * 100):.1f}" if total_chapters > 0 else "0.0"
                    
                    # Handle None values safely
                    char_str = project.character_setting or ""
                    world_str = project.world_setting or ""
                    plot_str = project.plot_idea or ""

                    char_fmt = char_str[:100] + "..." if len(char_str) > 100 else char_str
                    world_fmt = world_str[:100] + "..." if len(world_str) > 100 else world_str
                    plot_fmt = plot_str[:100] + "..." if len(plot_str) > 100 else plot_str

                    # Logic fallback
                    info_template = t("continue_tab.info_template")
                    if isinstance(info_template, str) and '{' in info_template:
                        info = info_template.format(
                            title=project.title,
                            genre=project.genre,
                            completed=completed,
                            total=total_chapters,
                            words=project.get_total_words(),
                            percent=percent,
                            char=char_fmt,
                            world=world_fmt,
                            plot=plot_fmt
                        )
                    else:
                        info = f"### 📖 {project.title}\n**Thể loại**: {project.genre}\n**Tiến độ**: {percent}% ({completed}/{total_chapters} chương)\n**Tổng số từ**: {project.get_total_words()}\n💡 Chương tiếp theo: {next_ch}"
                    
                    # Format the outline list
                    outline_lines = []
                    for ch in project.chapters:
                        status = "✅" if getattr(ch, 'content', None) else "⬜"
                        outline_lines.append(f"{status} Chương {ch.num}: {ch.title} - {ch.desc}")
                    outline_text = "\n".join(outline_lines)
                    if not outline_text:
                        outline_text = "Dự án này chưa có dàn ý chi tiết."

                    # Generate chapter choices
                    chapter_choices = [f"Chương {ch.num}: {ch.title}" for ch in project.chapters if getattr(ch, 'content', None)]

                    return info, next_ch, outline_text, chapter_choices
                return f"❌ {msg}", 1, "Chưa tải dự án...", []
            except Exception as e:
                return f"❌ {str(e)}", 1, "Lỗi khi tải dàn ý", []

        def on_continue_chapter_select(chapter_title):
            if not chapter_title or not app_state.current_project:
                return ""
            for ch in app_state.current_project.chapters:
                if f"Chương {ch.num}: {ch.title}" == chapter_title:
                    return ch.content or ""
            return ""

        def on_continue_generate(project_title, ch_num, ch_title, ch_desc, target_words, custom_prompt, mem_type, mem_chaps, use_reflection, selected_style):
            yield "⏳ Đang chuẩn bị dữ liệu...", "", gr.update(interactive=False), gr.update(), gr.update()
            if not app_state.current_project:
                yield f"❌ {t('continue_tab.no_project_selected')}", "", gr.update(interactive=True), gr.update(), gr.update()
                return

            gen = app_state.get_generator()
            if selected_style:
                gen.config.generation.writing_style = selected_style
            project = app_state.current_project

            # Check if the requested chapter exists in the outline
            if not any(int(ch.num) == int(ch_num) for ch in project.chapters):
                yield f"❌ Lỗi: Chương {int(ch_num)} không có trong dàn ý. Tab này chỉ hỗ trợ hoàn thành nốt nội dung dàn ý đã có, không viết thêm chương mới.", "", gr.update(interactive=True), gr.update(), gr.update()
                return

            # Get completed past chapters mapped linearly
            all_past_chapters = [ch for ch in project.chapters if ch.num < int(ch_num) and getattr(ch, 'content', None)]
            mem_ch = int(mem_chaps) if mem_chaps else 3
            past_chapters = all_past_chapters[-mem_ch:] if len(all_past_chapters) > mem_ch else all_past_chapters

            prev_content = ""
            context_summary = ""

            if mem_type == "Toàn văn":
                prev_texts = [c.content for c in past_chapters]
                prev_content = "\n\n".join(prev_texts)
                prev_content = prev_content[-4000:]
            else:
                summaries = []
                for c in past_chapters:
                    if not hasattr(c, 'summary') or not c.summary:
                        yield f"⏳ Đang tạo tóm tắt ngữ cảnh cho chương {c.num}...", ""
                        summ, _ = gen.generate_chapter_summary(c.content, c.title)
                        c.summary = summ
                    if c.summary:
                        summaries.append(f"Chương {c.num} - {c.title}: {c.summary}")
                
                if summaries:
                    context_summary = "\n".join(summaries)
                
                if all_past_chapters:
                    prev_content = all_past_chapters[-1].content[-1500:]

            yield f"⏳ {t('streaming.generating_single', num=int(ch_num))}", "", gr.update(interactive=False), gr.update(), gr.update()

            # Dùng streaming để hiển thị nội dung trực tiếp
            accumulated = ""
            stream_ok = False
            stream_err = ""
            for success, chunk in gen.generate_chapter_stream(
                chapter_num=int(ch_num), chapter_title=ch_title,
                chapter_desc=ch_desc, novel_title=project.title,
                character_setting=project.character_setting,
                world_setting=project.world_setting,
                plot_idea=project.plot_idea, genre=project.genre,
                sub_genres=project.sub_genres,
                previous_content=prev_content, context_summary=context_summary, custom_prompt=custom_prompt,
                use_reflection=use_reflection
            ):
                if success:
                    accumulated += chunk
                    stream_ok = True
                    word_count = len(accumulated.split())
                    stream_label = t("streaming.words_live", num=int(ch_num), words=word_count)
                    yield f"✍️ {stream_label}", accumulated, gr.update(interactive=False), gr.update(), gr.update()
                else:
                    stream_err = chunk

            content = accumulated if stream_ok else ""
            msg = stream_err if not stream_ok else ""

            if content:
                new_ch = Chapter(
                    num=int(ch_num), title=ch_title, desc=ch_desc,
                    content=content, word_count=len(content),
                    generated_at=datetime.now().isoformat()
                )
                found = False
                for i, ch in enumerate(project.chapters):
                    if ch.num == int(ch_num):
                        project.chapters[i] = new_ch
                        found = True
                        break
                if not found:
                    project.chapters.append(new_ch)
                    project.chapters.sort(key=lambda x: x.num)

                ProjectManager.save_project(project)
                
                # Format the outline list
                outline_lines = []
                for ch in project.chapters:
                    status = "✅" if getattr(ch, 'content', None) else "⬜"
                    outline_lines.append(f"{status} Chương {ch.num}: {ch.title} - {ch.desc}")
                outline_text = "\n".join(outline_lines)
                
                # Update choices
                chapter_choices = [f"Chương {ch.num}: {ch.title}" for ch in project.chapters if getattr(ch, 'content', None)]
                selected_choice = f"Chương {int(ch_num)}: {ch_title}"
                
                yield f"✅ Chương {int(ch_num)} đã sinh ({len(content)} từ)", content, gr.update(interactive=True), gr.update(value=outline_text), gr.update(choices=chapter_choices, value=selected_choice)
            else:
                yield f"❌ {msg}", "", gr.update(interactive=True), gr.update(), gr.update()

        def on_continue_auto_generate(project_title, target_words, custom_prompt, mem_type, mem_chaps, use_reflection, selected_style, progress=gr.Progress()):
            yield "⏳ Đang chuẩn bị dữ liệu...", "", gr.update(interactive=False), gr.update(interactive=False), gr.update(), gr.update()
            if not app_state.current_project:
                yield f"❌ {t('continue_tab.no_project_selected')}", "", gr.update(interactive=True), gr.update(interactive=True), gr.update(), gr.update()
                return

            gen = app_state.get_generator()
            if selected_style:
                gen.config.generation.writing_style = selected_style
            project = app_state.current_project
            app_state.is_generating = True
            app_state.stop_requested = False

            blank_chapters = [ch for ch in project.chapters if not getattr(ch, 'content', None)]
            if not blank_chapters:
                yield "✅ Đã viết xong tất cả các chương trong dàn ý!", "", gr.update(interactive=True), gr.update(interactive=True), gr.update(), gr.update()
                return

            results = [f"📋 Phát hiện {len(blank_chapters)} chương chưa viết. Bắt đầu tự động tạo..."]
            yield "\n".join(results), "", gr.update(interactive=False), gr.update(interactive=False), gr.update(), gr.update()

            last_content = ""

            for i, ch in enumerate(blank_chapters):
                if app_state.stop_requested:
                    results.append("\n⚠️ Đã dừng sinh tự động!")
                    yield "\n".join(results), last_content, gr.update(interactive=True), gr.update(interactive=True), gr.update(), gr.update()
                    break

                results.append(f"\n✍️ Đang sinh Chương {ch.num}: {ch.title}...")
                progress((i + 1) / len(blank_chapters))
                yield "\n".join(results), last_content, gr.update(interactive=False), gr.update(interactive=False), gr.update(), gr.update()

                all_past_chapters = [past for past in project.chapters if past.num < ch.num and getattr(past, 'content', None)]
                mem_ch = int(mem_chaps) if mem_chaps else 3
                past_chapters = all_past_chapters[-mem_ch:] if len(all_past_chapters) > mem_ch else all_past_chapters

                prev_content = ""
                context_summary = ""

                if mem_type == "Toàn văn":
                    prev_texts = [c.content for c in past_chapters]
                    prev_content = "\n\n".join(prev_texts)
                    prev_content = prev_content[-4000:]
                else:
                    summaries = []
                    for c in past_chapters:
                        if not hasattr(c, 'summary') or not c.summary:
                            summ, _ = gen.generate_chapter_summary(c.content, c.title)
                            c.summary = summ
                        if c.summary:
                            summaries.append(f"Chương {c.num} - {c.title}: {c.summary}")
                    
                    if summaries:
                        context_summary = "\n".join(summaries)
                    
                    if all_past_chapters:
                        prev_content = all_past_chapters[-1].content[-1500:]

                # Dùng streaming để hiển thị nội dung trực tiếp
                accumulated = ""
                stream_ok = False
                stream_err = ""
                for success, chunk in gen.generate_chapter_stream(
                    chapter_num=int(ch.num), chapter_title=ch.title,
                    chapter_desc=ch.desc, novel_title=project.title,
                    character_setting=project.character_setting,
                    world_setting=project.world_setting,
                    plot_idea=project.plot_idea, genre=project.genre,
                    sub_genres=project.sub_genres,
                    previous_content=prev_content, context_summary=context_summary, custom_prompt=custom_prompt,
                    use_reflection=use_reflection
                ):
                    if success:
                        accumulated += chunk
                        stream_ok = True
                        word_count = len(accumulated.split())
                        stream_label = t("streaming.words_live", num=int(ch.num), words=word_count)
                        status_lines = results + [f"  📝 {stream_label}"]
                        yield "\n".join(status_lines), accumulated, gr.update(interactive=False), gr.update(interactive=False), gr.update(), gr.update()
                    else:
                        stream_err = chunk

                content = accumulated if stream_ok else ""
                msg = stream_err if not stream_ok else ""

                if content:
                    ch.content = content
                    ch.word_count = len(content.split())
                    ch.generated_at = datetime.now().isoformat()
                    ProjectManager.save_project(project)
                    last_content = content

                    # Format the outline list
                    outline_lines = []
                    for pr_ch in project.chapters:
                        status = "✅" if getattr(pr_ch, 'content', None) else "⬜"
                        outline_lines.append(f"{status} Chương {pr_ch.num}: {pr_ch.title} - {pr_ch.desc}")
                    outline_text = "\n".join(outline_lines)

                    # Update choices
                    chapter_choices = [f"Chương {c2.num}: {c2.title}" for c2 in project.chapters if getattr(c2, 'content', None)]
                    selected_choice = f"Chương {ch.num}: {ch.title}"

                    results.append(f"✅ Chương {ch.num} hoàn tất ({ch.word_count} từ)")
                    yield "\n".join(results), content, gr.update(interactive=False), gr.update(interactive=False), gr.update(value=outline_text), gr.update(choices=chapter_choices, value=selected_choice)
                else:
                    results.append(f"❌ Lỗi ở chương {ch.num}: {msg}")
                    app_state.stop_requested = True
                    yield "\n".join(results), last_content, gr.update(interactive=True), gr.update(interactive=True), gr.update(), gr.update()
                    break

            app_state.is_generating = False
            results.append("\n🎉 Hoàn thành chuỗi viết tự động!")
            yield "\n".join(results), last_content, gr.update(interactive=True), gr.update(interactive=True), gr.update(), gr.update()

        def on_continue_stop():
            app_state.stop_requested = True
            return "⏸️ Đang dừng..."

        def on_batch_summary(project_title):
            if not project_title:
                yield "❌ Please select a project first."
                return
            project_data = ProjectManager.get_project_by_title(project_title)
            if not project_data:
                yield "❌ Project not found."
                return
            results = []
            for msg in batch_generate_summaries(project_data["id"]):
                results.append(msg)
                yield "\n".join(results)

        batch_summary_btn.click(
            fn=on_batch_summary,
            inputs=[continue_project_selector],
            outputs=[batch_summary_progress]
        )

        refresh_continue_btn.click(
            fn=on_refresh_continue, 
            inputs=[continue_project_selector], 
            outputs=[continue_project_selector, continue_project_info, continue_chapter_num, continue_outline_display, continue_chapter_selector]
        )
        continue_project_selector.change(
            fn=on_continue_project_select,
            inputs=[continue_project_selector],
            outputs=[continue_project_info, continue_chapter_num, continue_outline_display, continue_chapter_selector]
        )
        continue_chapter_selector.change(
            fn=on_continue_chapter_select,
            inputs=[continue_chapter_selector],
            outputs=[continue_content_display]
        )
        continue_generate_btn.click(
            fn=on_continue_generate,
            inputs=[continue_project_selector, continue_chapter_num, continue_chapter_title,
                    continue_chapter_desc, continue_target_words, continue_custom_prompt, memory_type, memory_chapters, use_reflection_checkbox, continue_style_dropdown],
            outputs=[continue_status, continue_content_display, continue_generate_btn, continue_outline_display, continue_chapter_selector]
        )
        continue_auto_btn.click(
            fn=on_continue_auto_generate,
            inputs=[continue_project_selector, continue_target_words, continue_custom_prompt, memory_type, memory_chapters, use_reflection_checkbox, continue_style_dropdown],
            outputs=[continue_status, continue_content_display, continue_auto_btn, continue_generate_btn, continue_outline_display, continue_chapter_selector],
            show_progress="full"
        )
        continue_stop_btn.click(
            fn=on_continue_stop,
            outputs=[continue_status]
        )

        # Kết nối sự kiện: Phân tích tiểu thuyết
        analyze_btn.click(
            fn=on_analyze_novel,
            inputs=[analyzer_file],
            outputs=[analyze_status, analyzer_result],
        )

        # Kết nối sự kiện: Phát hiện & lấp đầy khoảng trống
        detect_gaps_btn.click(
            fn=on_detect_gaps,
            inputs=[continue_project_selector],
            outputs=[gaps_display],
        )
        fill_all_btn.click(
            fn=on_fill_all_gaps,
            inputs=[continue_project_selector],
            outputs=[fill_progress],
        )

        # Kết nối sự kiện: Hồ sơ nhân vật
        continue_project_selector.change(
            fn=on_load_characters,
            inputs=[continue_project_selector],
            outputs=[char_table],
        )
        char_save_btn.click(
            fn=on_save_character,
            inputs=[continue_project_selector, char_name, char_role, char_appearance,
                    char_personality, char_relationships, char_arc_notes, char_first_ch],
            outputs=[char_status, char_table],
        )
        char_delete_btn.click(
            fn=on_delete_character,
            inputs=[continue_project_selector, char_name],
            outputs=[char_status, char_table],
        )
