"""Rewrite and Polish tools — embedded in Continue tab as an accordion."""
import gradio as gr
from locales.i18n import t
from services.genre_manager import GenreManager
from services.style_manager import StyleManager
from utils.file_parser import parse_novel_file
from core.state import app_state


def build_text_tools_section():
    """Build the Rewrite + Polish accordion. Call inside continue_tab's Tab context."""
    with gr.Accordion(t("continue_tab.text_tools"), open=False):
        tool_mode = gr.Radio(
            choices=[t("tabs.rewrite"), t("tabs.polish")],
            value=t("tabs.rewrite"),
            label=t("continue_tab.tool_mode")
        )

        tool_file_input = gr.File(
            label=t("rewrite.upload_file"),
            file_types=[".txt", ".docx", ".md", ".pdf"]
        )
        tool_text_input = gr.Textbox(
            label=t("polish.original_text"),
            lines=8, placeholder=""
        )

        # Rewrite-specific options
        genre_choices = GenreManager.get_genre_names()
        style_choices = StyleManager.get_style_names()
        with gr.Row(visible=True) as rewrite_options:
            tool_genre = gr.Dropdown(
                choices=genre_choices,
                label=t("create.genre_label"),
                value=genre_choices[0] if genre_choices else None,
                interactive=True, scale=1
            )
            tool_style = gr.Dropdown(
                choices=style_choices,
                label=t("rewrite.preset_style"),
                value=style_choices[0] if style_choices else None,
                interactive=True, scale=1
            )

        # Polish-specific options
        tool_custom_req = gr.Textbox(
            label=t("polish.custom_req"),
            placeholder=t("polish.custom_req_placeholder"),
            lines=2, visible=False
        )

        tool_reflection = gr.Checkbox(
            label=t("continue_tab.self_reflection"),
            value=False
        )

        with gr.Row():
            tool_run_btn = gr.Button(t("continue_tab.run_tool"), variant="primary")
            tool_suggest_btn = gr.Button(t("polish.polish_suggest_btn"), visible=False, variant="secondary")

        tool_status = gr.Textbox(label=t("rewrite.parse_status"), interactive=False)
        tool_output = gr.Textbox(lines=12, interactive=True, elem_classes=["novel-text"])

        # --- Mode toggling ---
        def on_mode_change(mode):
            is_rewrite = (mode == t("tabs.rewrite"))
            return (
                gr.update(visible=is_rewrite),    # rewrite_options row
                gr.update(visible=not is_rewrite), # tool_custom_req
                gr.update(visible=not is_rewrite), # tool_suggest_btn
            )

        tool_mode.change(
            fn=on_mode_change,
            inputs=[tool_mode],
            outputs=[rewrite_options, tool_custom_req, tool_suggest_btn]
        )

        # --- File upload ---
        def on_tool_file_upload(file):
            if file is None:
                return ""
            try:
                content = parse_novel_file(file.name)
                return content
            except Exception as e:
                return f"❌ {str(e)}"

        tool_file_input.change(
            fn=on_tool_file_upload,
            inputs=[tool_file_input],
            outputs=[tool_text_input]
        )

        # --- Run tool ---
        def on_tool_run(mode, text, genre, style, custom_req, use_reflection):
            gen = app_state.get_generator()
            if mode == t("tabs.rewrite"):
                yield "⏳ Đang gọi AI xử lý... Vui lòng chờ.", gr.update(), gr.update(interactive=False)
                instructions = f"Thể loại: {genre}\nPhong cách thiết lập: {style}"
                content, msg = gen.rewrite_paragraph(text, instructions, use_reflection=use_reflection)
                if content:
                    yield f"✅ {msg}", content, gr.update(interactive=True)
                else:
                    yield f"❌ {msg}", gr.update(), gr.update(interactive=True)
            else:
                yield "⏳ Đang gọi AI xử lý... Vui lòng chờ.", gr.update(), gr.update(interactive=False)
                content, msg = gen.polish_text(text, custom_requirements=custom_req, use_reflection=use_reflection)
                if content:
                    yield f"✅ {msg}", content, gr.update(interactive=True)
                else:
                    yield f"❌ {msg}", gr.update(), gr.update(interactive=True)

        tool_run_btn.click(
            fn=on_tool_run,
            inputs=[tool_mode, tool_text_input, tool_genre, tool_style, tool_custom_req, tool_reflection],
            outputs=[tool_status, tool_output, tool_run_btn]
        )

        # --- Polish suggest ---
        def on_tool_suggest(text, custom_req, use_reflection):
            yield "⏳ Đang gọi AI xử lý... Vui lòng chờ.", gr.update(), gr.update(interactive=False)
            gen = app_state.get_generator()
            content, msg = gen.polish_and_suggest(text, custom_requirements=custom_req, use_reflection=use_reflection)
            if content:
                yield f"✅ {msg}", content, gr.update(interactive=True)
            else:
                yield f"❌ {msg}", gr.update(), gr.update(interactive=True)

        tool_suggest_btn.click(
            fn=on_tool_suggest,
            inputs=[tool_text_input, tool_custom_req, tool_reflection],
            outputs=[tool_status, tool_output, tool_suggest_btn]
        )
