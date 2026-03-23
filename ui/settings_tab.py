import gradio as gr
from locales.i18n import t
from core.config import get_config, API_PROVIDERS
from services.cost_tracker import CostTracker
from core.config_api import ConfigAPIManager
from services.api_client import get_api_client, reinit_api_client
from services.novel_generator import get_cache_size, list_generation_caches, clear_generation_cache
from services.genre_manager import GenreManager
from services.sub_genre_manager import SubGenreManager
from services.style_manager import StyleManager
from core.state import app_state
from utils.api_key_detector import detect_provider_from_key

# ---------------------------------------------------------------------------
# Generation presets
# ---------------------------------------------------------------------------
GENERATION_PRESETS = {
    "creative": {"temperature": 1.2, "top_p": 0.95, "max_tokens": 16000, "chapter_target_words": 3000},
    "balanced": {"temperature": 0.8, "top_p": 0.9, "max_tokens": 8000, "chapter_target_words": 2000},
    "precise": {"temperature": 0.5, "top_p": 0.8, "max_tokens": 4000, "chapter_target_words": 1500},
}


def build_settings_tab():
    with gr.Tab(t("tabs.settings")):
        gr.Markdown(f"### {t('settings.header')}")

        with gr.Tabs():

            # ==================================================================
            # Sub-tab 1: API Backends
            # ==================================================================
            with gr.Tab(t("settings.tab_backends")):
                gr.Markdown(f"### {t('settings.backends_header')}")

                # ------------------------------------------------------------------
                # Helper: display all backends as markdown
                # ------------------------------------------------------------------
                def get_backends_display():
                    try:
                        result = ConfigAPIManager.list_backends()
                        if result["success"] and result["data"]:
                            lines = [f"#### 📋 {len(result['data'])} backend(s)\n"]
                            for b in result["data"]:
                                enabled = "✅" if b.get("enabled") else "❌"
                                default = " ⭐" if b.get("is_default") else ""
                                lines.append(f"{enabled} **{b['name']}**{default}")
                                lines.append(f"  - Model: `{b.get('model', '')}`")
                                lines.append(f"  - URL: `{b.get('base_url', '')[:50]}...`")
                                lines.append(f"  - Timeout: {b.get('timeout', 30)}s")
                                lines.append("")
                            return "\n".join(lines)
                        return t("app.no_backends_warning")
                    except Exception as e:
                        return f"❌ {str(e)}"

                # ------------------------------------------------------------------
                # Quick API Key Detection row
                # ------------------------------------------------------------------
                gr.Markdown(f"#### {t('settings.quick_add_header')}")
                with gr.Row():
                    quick_key_input = gr.Textbox(
                        label=t("settings.quick_key_label"),
                        placeholder=t("settings.quick_key_placeholder"),
                        scale=4,
                        type="password",
                    )
                    quick_detect_btn = gr.Button("🔍", variant="secondary", scale=1)
                    quick_add_btn = gr.Button(t("settings.quick_add_btn"), variant="primary", scale=1)

                quick_detect_result = gr.Markdown("")
                quick_add_status = gr.Textbox(label=t("settings.operation_result"), interactive=False, visible=False)

                # ------------------------------------------------------------------
                # Advanced config accordion (existing full form)
                # ------------------------------------------------------------------
                with gr.Accordion(t("settings.advanced_config"), open=False):
                    with gr.Row():
                        # Cột trái: danh sách + test + delete
                        with gr.Column(scale=1):
                            with gr.Group():
                                backends_display = gr.Markdown("...")
                                api_refresh_btn = gr.Button(t("settings.refresh_list"), size="sm")

                            with gr.Group():
                                gr.Markdown(f"#### {t('settings.test_manage_header')}")
                                with gr.Row():
                                    test_name_input = gr.Textbox(
                                        label=t("settings.test_backend_name"),
                                        placeholder=t("settings.test_backend_placeholder"),
                                        scale=2,
                                    )
                                    api_test_btn = gr.Button(t("settings.test_btn"), variant="secondary", scale=1)
                                test_result = gr.Textbox(label=t("settings.test_result"), interactive=False)

                                gr.Markdown("---")
                                with gr.Row():
                                    delete_name_input = gr.Textbox(
                                        label=t("settings.delete_backend_name"),
                                        placeholder=t("settings.delete_backend_placeholder"),
                                        scale=2,
                                    )
                                    api_delete_btn = gr.Button(t("settings.delete_btn"), variant="stop", scale=1)

                        # Cột phải: form thêm / sửa
                        with gr.Column(scale=2):
                            with gr.Group():
                                gr.Markdown(f"#### {t('settings.edit_config_header')} ({t('settings.add_backend_header')})")

                                provider_names = [API_PROVIDERS[k]["name"] for k in API_PROVIDERS]

                                with gr.Row():
                                    manage_backend_select = gr.Dropdown(
                                        choices=[b['name'] for b in ConfigAPIManager.list_backends().get("data", [])],
                                        label=t("settings.select_backend_edit"),
                                        interactive=True,
                                        scale=4,
                                    )
                                    manage_backend_btn = gr.Button(t("settings.select_btn"), variant="secondary", scale=1)

                                with gr.Row():
                                    api_provider_dropdown = gr.Dropdown(
                                        choices=provider_names,
                                        label=t("settings.provider_label"),
                                        info=t("settings.provider_info"),
                                        interactive=True,
                                    )

                                with gr.Row():
                                    api_name_input = gr.Textbox(
                                        label=t("settings.backend_name"),
                                        placeholder=t("settings.backend_name_placeholder"),
                                    )
                                    api_type_dropdown = gr.Dropdown(
                                        choices=ConfigAPIManager.get_backend_types(),
                                        value="openai",
                                        label=t("settings.backend_type"),
                                        interactive=True,
                                    )

                                with gr.Row():
                                    api_url_input = gr.Textbox(
                                        label=t("settings.base_url"),
                                        placeholder=t("settings.base_url_placeholder"),
                                    )
                                    api_key_input = gr.Textbox(
                                        label=t("settings.api_key"),
                                        placeholder=t("settings.api_key_placeholder"),
                                        type="password",
                                    )

                                with gr.Row():
                                    api_model_input = gr.Textbox(
                                        label=t("settings.model_name"),
                                        placeholder=t("settings.model_name_placeholder"),
                                    )
                                    api_timeout_input = gr.Slider(
                                        minimum=5, maximum=600, value=120, step=5,
                                        label=t("settings.timeout"),
                                    )

                                with gr.Row():
                                    api_save_btn = gr.Button(t("settings.add_btn"), variant="primary")
                                    api_update_btn = gr.Button(t("settings.update_btn"), variant="secondary")

                                api_status = gr.Textbox(label=t("settings.operation_result"), interactive=False)

                # ------------------------------------------------------------------
                # Event handlers — API Backends
                # ------------------------------------------------------------------
                def on_quick_detect(api_key):
                    result = detect_provider_from_key(api_key)
                    if result:
                        return f"**Detected:** {result['name']} → Model: `{result['model']}`"
                    if api_key.strip():
                        return "⚠️ Unknown provider. Use Advanced config below."
                    return ""

                def on_quick_add(api_key):
                    result = detect_provider_from_key(api_key)
                    if not result:
                        return "❌ Cannot auto-detect provider. Use Advanced config.", get_backends_display(), gr.update()
                    name = result["name"]
                    existing = [b['name'] for b in ConfigAPIManager.list_backends().get("data", [])]
                    final_name = name
                    i = 2
                    while final_name in existing:
                        final_name = f"{name} {i}"
                        i += 1
                    save_result = ConfigAPIManager.add_backend(
                        final_name, "openai", result["base_url"], api_key.strip(), result["model"], 120
                    )
                    reinit_api_client()
                    app_state.generator = None
                    new_choices = [b['name'] for b in ConfigAPIManager.list_backends().get("data", [])]
                    return save_result["message"], get_backends_display(), gr.update(choices=new_choices)

                def on_provider_select(provider_name):
                    for key, info in API_PROVIDERS.items():
                        if info["name"] == provider_name:
                            return info.get("base_url", ""), info.get("default_model", ""), provider_name
                    return "", "", provider_name

                def on_api_test(name):
                    yield "⏳ Đang kiểm tra kết nối API... Vui lòng chờ."
                    result = ConfigAPIManager.test_backend(name)
                    yield result["message"]

                def on_api_save(name, btype, url, key, model, timeout):
                    if not name.strip():
                        return "❌ Vui lòng nhập tên giao diện", get_backends_display(), gr.update()
                    result = ConfigAPIManager.add_backend(name, btype, url, key, model, int(timeout))
                    reinit_api_client()
                    app_state.generator = None
                    new_choices = [b['name'] for b in ConfigAPIManager.list_backends().get("data", [])]
                    return result["message"], get_backends_display(), gr.update(choices=new_choices)

                def on_api_update(old_name, new_name, btype, url, key, model, timeout):
                    if not old_name:
                        return "❌ Vui lòng chọn một cấu hình để chỉnh sửa trước", get_backends_display(), gr.update()
                    if not new_name.strip():
                        return "❌ Vui lòng nhập tên giao diện", get_backends_display(), gr.update()
                    result = ConfigAPIManager.update_backend(
                        old_name,
                        name=new_name.strip(),
                        type=btype,
                        base_url=url,
                        api_key=key,
                        model=model,
                        timeout=int(timeout),
                    )
                    reinit_api_client()
                    app_state.generator = None
                    new_choices = [b['name'] for b in ConfigAPIManager.list_backends().get("data", [])]
                    new_val = new_name.strip() if result["success"] else old_name
                    return result["message"], get_backends_display(), gr.update(choices=new_choices, value=new_val)

                def on_backend_select(selected_name):
                    if not selected_name:
                        return (gr.update(value=""), gr.update(value="openai"), gr.update(value=""),
                                gr.update(value=""), gr.update(value=""), gr.update(value=120))
                    backends = ConfigAPIManager.list_backends().get("data", [])
                    for b in backends:
                        if b["name"] == selected_name:
                            return (
                                gr.update(value=b.get("name", "")),
                                gr.update(value=b.get("type", "openai")),
                                gr.update(value=b.get("base_url", "")),
                                gr.update(value=b.get("api_key", "")),
                                gr.update(value=b.get("model", "")),
                                gr.update(value=b.get("timeout", 120)),
                            )
                    return (gr.update(value=""), gr.update(value="openai"), gr.update(value=""),
                            gr.update(value=""), gr.update(value=""), gr.update(value=120))

                def on_api_delete(name):
                    result = ConfigAPIManager.delete_backend(name)
                    reinit_api_client()
                    app_state.generator = None
                    new_choices = [b['name'] for b in ConfigAPIManager.list_backends().get("data", [])]
                    return result["message"], get_backends_display(), gr.update(choices=new_choices)

                def force_refresh_backends():
                    choices = [b['name'] for b in ConfigAPIManager.list_backends().get("data", [])]
                    return get_backends_display(), gr.update(choices=choices)

                # Wire quick-detect events
                quick_detect_btn.click(fn=on_quick_detect, inputs=[quick_key_input], outputs=[quick_detect_result])
                quick_add_btn.click(
                    fn=on_quick_add,
                    inputs=[quick_key_input],
                    outputs=[quick_add_status, backends_display, manage_backend_select],
                )
                quick_add_btn.click(lambda: gr.update(visible=True), outputs=[quick_add_status])

                # Wire advanced form events
                api_provider_dropdown.change(
                    fn=on_provider_select,
                    inputs=[api_provider_dropdown],
                    outputs=[api_url_input, api_model_input, api_name_input],
                )
                manage_backend_btn.click(
                    fn=on_backend_select,
                    inputs=[manage_backend_select],
                    outputs=[api_name_input, api_type_dropdown, api_url_input, api_key_input, api_model_input, api_timeout_input],
                )
                api_save_btn.click(
                    fn=on_api_save,
                    inputs=[api_name_input, api_type_dropdown, api_url_input, api_key_input, api_model_input, api_timeout_input],
                    outputs=[api_status, backends_display, manage_backend_select],
                )
                api_update_btn.click(
                    fn=on_api_update,
                    inputs=[manage_backend_select, api_name_input, api_type_dropdown, api_url_input, api_key_input, api_model_input, api_timeout_input],
                    outputs=[api_status, backends_display, manage_backend_select],
                )
                api_test_btn.click(fn=on_api_test, inputs=[test_name_input], outputs=[test_result])
                api_delete_btn.click(
                    fn=on_api_delete,
                    inputs=[delete_name_input],
                    outputs=[api_status, backends_display, manage_backend_select],
                )
                api_refresh_btn.click(fn=force_refresh_backends, outputs=[backends_display, manage_backend_select])

            # ==================================================================
            # Sub-tab 2: Generation (params + presets + cost tracker)
            # ==================================================================
            with gr.Tab(t("settings.tab_params")):

                # --- Presets ---
                gr.Markdown(f"#### {t('settings.presets_header')}")
                preset_radio = gr.Radio(
                    choices=[
                        t("settings.preset_creative"),
                        t("settings.preset_balanced"),
                        t("settings.preset_precise"),
                    ],
                    label=t("settings.presets_label"),
                    value=None,
                )
                preset_status = gr.Textbox(label=t("settings.save_status"), interactive=False, visible=False)

                # --- Custom params accordion ---
                with gr.Accordion(t("settings.custom_params"), open=False):
                    with gr.Group():
                        gr.Markdown(f"#### {t('settings.params_header')}")

                        config = get_config()
                        gen_config = config.generation

                        with gr.Row():
                            param_temperature = gr.Slider(
                                minimum=0.1, maximum=2.0, value=gen_config.temperature, step=0.1,
                                label=t("settings.temperature_label"), info=t("settings.temperature_info"),
                            )
                            param_top_p = gr.Slider(
                                minimum=0.1, maximum=1.0, value=gen_config.top_p, step=0.05,
                                label="Top P", info=t("settings.top_p_info"),
                            )

                        with gr.Row():
                            param_max_tokens = gr.Slider(
                                minimum=100, maximum=100000, value=gen_config.max_tokens, step=100,
                                label="Max Tokens", info=t("settings.max_tokens_info"),
                            )
                            param_chapter_words = gr.Slider(
                                minimum=500, maximum=65536, value=gen_config.chapter_target_words, step=500,
                                label=t("settings.chapter_target_words"),
                            )

                        with gr.Row():
                            param_writing_style = gr.Dropdown(
                                choices=StyleManager.get_style_names(),
                                value=gen_config.writing_style,
                                label=t("settings.writing_style"),
                                allow_custom_value=True,
                            )
                            param_writing_tone = gr.Dropdown(
                                choices=t("settings.tones"),
                                value=gen_config.writing_tone,
                                label=t("settings.tone_label"),
                                allow_custom_value=True,
                            )

                        with gr.Row():
                            param_char_dev = gr.Dropdown(
                                choices=t("settings.char_dev_options"),
                                value=gen_config.character_development,
                                label=t("settings.char_dev_label"),
                                allow_custom_value=True,
                            )
                            param_plot_complexity = gr.Dropdown(
                                choices=t("settings.plot_complexity_options"),
                                value=gen_config.plot_complexity,
                                label=t("settings.plot_complexity_label"),
                                allow_custom_value=True,
                            )

                        save_params_btn = gr.Button(t("settings.save_params_btn"), variant="primary")
                        params_status = gr.Textbox(label=t("settings.save_status"), interactive=False)

                # --- Cost tracker accordion ---
                with gr.Accordion(f"💰 {t('cost_tracker.tab_label')}", open=False):
                    gr.Markdown(f"#### {t('cost_tracker.total_header')}")
                    cost_summary_md = gr.Markdown(t("cost_tracker.no_data"))

                    with gr.Row():
                        cost_refresh_btn = gr.Button(t("cost_tracker.refresh_btn"), size="sm")

                    gr.Markdown(f"#### {t('cost_tracker.by_project_header')}")
                    cost_by_project_df = gr.Dataframe(
                        headers=[
                            t("cost_tracker.col_project"),
                            t("cost_tracker.col_tokens_in"),
                            t("cost_tracker.col_tokens_out"),
                            t("cost_tracker.col_cost"),
                            t("cost_tracker.col_calls"),
                        ],
                        datatype=["str", "number", "number", "number", "number"],
                        interactive=False,
                    )

                    gr.Markdown(f"#### {t('cost_tracker.by_backend_header')}")
                    cost_by_backend_df = gr.Dataframe(
                        headers=[
                            t("cost_tracker.col_backend"),
                            t("cost_tracker.col_model"),
                            t("cost_tracker.col_tokens_in"),
                            t("cost_tracker.col_tokens_out"),
                            t("cost_tracker.col_cost"),
                            t("cost_tracker.col_calls"),
                        ],
                        datatype=["str", "str", "number", "number", "number", "number"],
                        interactive=False,
                    )

                # ------------------------------------------------------------------
                # Event handlers — Generation tab
                # ------------------------------------------------------------------
                def on_preset_select(preset_name):
                    preset_map = {
                        t("settings.preset_creative"): "creative",
                        t("settings.preset_balanced"): "balanced",
                        t("settings.preset_precise"): "precise",
                    }
                    key = preset_map.get(preset_name, "balanced")
                    p = GENERATION_PRESETS[key]
                    cfg = get_config()
                    cfg.update_generation_config(
                        temperature=p["temperature"],
                        top_p=p["top_p"],
                        max_tokens=p["max_tokens"],
                        chapter_target_words=p["chapter_target_words"],
                    )
                    app_state.generator = None
                    return p["temperature"], p["top_p"], p["max_tokens"], p["chapter_target_words"]

                def on_save_params(temp, top_p, max_tokens, chapter_words, style, tone, chardev, plotcomp):
                    cfg = get_config()
                    success, msg = cfg.update_generation_config(
                        temperature=temp, top_p=top_p,
                        max_tokens=int(max_tokens),
                        chapter_target_words=int(chapter_words),
                        writing_style=style,
                        writing_tone=tone,
                        character_development=chardev,
                        plot_complexity=plotcomp,
                    )
                    if success:
                        app_state.generator = None
                        return f"✅ {msg}"
                    return f"❌ {msg}"

                def on_cost_refresh():
                    totals = CostTracker.get_total_costs()
                    summary = (
                        f"- **{t('cost_tracker.total_tokens_in')}**: {totals['tokens_in']:,}\n"
                        f"- **{t('cost_tracker.total_tokens_out')}**: {totals['tokens_out']:,}\n"
                        f"- **{t('cost_tracker.total_cost')}**: ${totals['cost']:.4f}\n"
                        f"- **{t('cost_tracker.total_calls')}**: {totals['calls']:,}"
                    )
                    by_project = CostTracker.get_costs_by_project()
                    project_rows = [
                        [r["title"], r["tokens_in"], r["tokens_out"], round(r["cost"], 6), r["calls"]]
                        for r in by_project
                    ]
                    by_backend = CostTracker.get_costs_by_backend()
                    backend_rows = [
                        [r["backend_name"], r["model"], r["tokens_in"], r["tokens_out"], round(r["cost"], 6), r["calls"]]
                        for r in by_backend
                    ]
                    return summary, project_rows, backend_rows

                preset_radio.change(
                    fn=on_preset_select,
                    inputs=[preset_radio],
                    outputs=[param_temperature, param_top_p, param_max_tokens, param_chapter_words],
                )
                save_params_btn.click(
                    fn=on_save_params,
                    inputs=[param_temperature, param_top_p, param_max_tokens, param_chapter_words,
                            param_writing_style, param_writing_tone, param_char_dev, param_plot_complexity],
                    outputs=[params_status],
                )
                cost_refresh_btn.click(
                    fn=on_cost_refresh,
                    outputs=[cost_summary_md, cost_by_project_df, cost_by_backend_df],
                )

            # ==================================================================
            # Sub-tab 3: Content Library (genre + sub-genre + styles + analyzer + cache)
            # ==================================================================
            with gr.Tab(t("settings.tab_content_library")):

                # --- Genre Management ---
                with gr.Accordion(f"📚 {t('settings.tab_genre')}", open=False):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown(f"#### {t('settings.genre_desc')}")
                            genre_select = gr.Dropdown(
                                choices=GenreManager.get_genre_names(),
                                label=t("settings.genre_select"),
                                interactive=True,
                            )
                        with gr.Column(scale=2):
                            with gr.Group():
                                genre_name_input = gr.Textbox(
                                    label=t("settings.genre_name"),
                                    placeholder=t("settings.genre_name_placeholder"),
                                )
                                genre_desc_input = gr.Textbox(
                                    label=t("settings.genre_description"),
                                    placeholder=t("settings.genre_description_placeholder"),
                                    lines=3,
                                )
                                with gr.Row():
                                    genre_add_btn = gr.Button(t("settings.genre_add_btn"), variant="primary")
                                    genre_update_btn = gr.Button(t("settings.genre_update_btn"), variant="secondary")
                                    genre_delete_btn = gr.Button(t("settings.genre_delete_btn"), variant="stop")
                                genre_op_status = gr.Textbox(label=t("settings.genre_op_status"), interactive=False)

                # --- Sub-genre Management ---
                with gr.Accordion(f"🏷️ {t('settings.tab_sub_genre')}", open=False):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown(f"#### {t('settings.sub_genre_desc')}")
                            sub_genre_select = gr.Dropdown(
                                choices=SubGenreManager.get_sub_genre_names(),
                                label=t("settings.sub_genre_select"),
                                interactive=True,
                            )
                        with gr.Column(scale=2):
                            with gr.Group():
                                sub_genre_name_input = gr.Textbox(
                                    label=t("settings.sub_genre_name"),
                                    placeholder=t("settings.sub_genre_name_placeholder"),
                                )
                                sub_genre_desc_input = gr.Textbox(
                                    label=t("settings.sub_genre_description"),
                                    placeholder=t("settings.sub_genre_description_placeholder"),
                                    lines=3,
                                )
                                with gr.Row():
                                    sub_genre_add_btn = gr.Button(t("settings.sub_genre_add_btn"), variant="primary")
                                    sub_genre_update_btn = gr.Button(t("settings.sub_genre_update_btn"), variant="secondary")
                                    sub_genre_delete_btn = gr.Button(t("settings.sub_genre_delete_btn"), variant="stop")
                                sub_genre_op_status = gr.Textbox(label=t("settings.sub_genre_op_status"), interactive=False)

                # --- Writing Styles ---
                with gr.Accordion(t("settings.tab_styles"), open=False):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown(f"#### {t('settings.styles_desc')}")
                            style_select = gr.Dropdown(
                                choices=StyleManager.get_style_names(),
                                label=t("settings.style_select"),
                                interactive=True,
                            )
                        with gr.Column(scale=2):
                            with gr.Group():
                                style_name_input = gr.Textbox(label=t("settings.style_name"), placeholder="Ví dụ: Mượt mà tự nhiên...")
                                style_desc_input = gr.Textbox(
                                    label=t("settings.style_desc"),
                                    placeholder="Hướng dẫn chi tiết cách viết...",
                                    lines=3,
                                )
                                with gr.Row():
                                    style_add_btn = gr.Button(t("settings.style_add_btn"), variant="primary")
                                    style_update_btn = gr.Button(t("settings.style_update_btn"), variant="secondary")
                                    style_delete_btn = gr.Button(t("settings.style_delete_btn"), variant="stop")
                                style_op_status = gr.Textbox(label=t("settings.style_op_status"), interactive=False)

                # --- AI Style Analyzer ---
                with gr.Accordion(f"🤖 {t('settings.style_analyzer_header')}", open=False):
                    gr.Markdown(f"#### {t('settings.style_analyzer_desc')}")
                    analyzer_text_input = gr.Textbox(
                        label=t("settings.analyzer_paste_text"),
                        placeholder=t("settings.analyzer_paste_placeholder"),
                        lines=10,
                    )
                    analyzer_btn = gr.Button(t("settings.analyze_style_btn"), variant="primary")
                    analyzer_result_name = gr.Textbox(label=t("settings.analyzer_result_name"), interactive=True)
                    analyzer_result_desc = gr.Textbox(
                        label=t("settings.analyzer_result_desc"), interactive=True, lines=4
                    )
                    analyzer_save_btn = gr.Button(t("settings.save_style_btn"), variant="secondary")
                    analyzer_status = gr.Textbox(label=t("settings.operation_result"), interactive=False)

                # --- Cache Management ---
                with gr.Accordion(f"🗃️ {t('settings.tab_cache')}", open=False):
                    gr.Markdown(f"#### {t('settings.cache_header')}")
                    cache_info_display = gr.Markdown(t("ui.no_cache"))

                    def get_cache_info():
                        try:
                            api_client = get_api_client()
                            stats = api_client.get_cache_stats()
                            gen_caches = list_generation_caches()
                            gen_size_val = get_cache_size()
                            return (
                                f"### Thống kê bộ nhớ đệm\n"
                                f"- **API Cache**: {stats['total_entries']}/{stats['max_size']} ({stats['usage_rate']:.1f}%)\n"
                                f"- **Generation Cache**: {len(gen_caches)} files ({gen_size_val / 1024:.1f} KB)"
                            )
                        except Exception as e:
                            return f"❌ {str(e)}"

                    with gr.Row():
                        refresh_cache_btn = gr.Button(t("settings.refresh_cache"), size="sm")
                        clear_all_cache_btn = gr.Button(t("settings.clear_all"), variant="stop")
                    cache_op_status = gr.Textbox(label=t("settings.cache_op_status"), interactive=False)

                # ------------------------------------------------------------------
                # Event handlers — Content Library tab
                # ------------------------------------------------------------------
                def on_genre_select(name):
                    if name:
                        desc = GenreManager.get_genre_description(name)
                        return name, desc or ""
                    return "", ""

                def on_genre_add(name, desc):
                    if not name.strip():
                        return t("settings.genre_err_name_empty"), gr.update()
                    success = GenreManager.add_genre(name.strip(), desc.strip())
                    if success:
                        return t("settings.genre_add_success"), gr.update(choices=GenreManager.get_genre_names())
                    return t("settings.genre_err_exists"), gr.update()

                def on_genre_update(old_name, new_name, desc):
                    if not old_name:
                        return t("settings.genre_err_none_selected"), gr.update()
                    success = GenreManager.update_genre(old_name, new_name.strip(), desc.strip())
                    if success:
                        return t("settings.genre_update_success"), gr.update(choices=GenreManager.get_genre_names())
                    return t("settings.genre_err_update"), gr.update()

                def on_genre_delete(name):
                    if not name:
                        return t("settings.genre_err_none_selected"), gr.update()
                    success = GenreManager.delete_genre(name)
                    if success:
                        return t("settings.genre_delete_success"), gr.update(choices=GenreManager.get_genre_names())
                    return t("settings.genre_err_delete"), gr.update()

                def on_sub_genre_select(name):
                    if name:
                        desc = SubGenreManager.get_sub_genre_description(name)
                        return name, desc or ""
                    return "", ""

                def on_sub_genre_add(name, desc):
                    if not name.strip():
                        return t("settings.sub_genre_err_name_empty"), gr.update()
                    success = SubGenreManager.add_sub_genre(name.strip(), desc.strip())
                    if success:
                        return t("settings.sub_genre_add_success"), gr.update(choices=SubGenreManager.get_sub_genre_names())
                    return t("settings.sub_genre_err_exists"), gr.update()

                def on_sub_genre_update(old_name, new_name, desc):
                    if not old_name:
                        return t("settings.sub_genre_err_none_selected"), gr.update()
                    success = SubGenreManager.update_sub_genre(old_name, new_name.strip(), desc.strip())
                    if success:
                        return t("settings.sub_genre_update_success"), gr.update(choices=SubGenreManager.get_sub_genre_names())
                    return t("settings.sub_genre_err_update"), gr.update()

                def on_sub_genre_delete(name):
                    if not name:
                        return t("settings.sub_genre_err_none_selected"), gr.update()
                    success = SubGenreManager.delete_sub_genre(name)
                    if success:
                        return t("settings.sub_genre_delete_success"), gr.update(choices=SubGenreManager.get_sub_genre_names())
                    return t("settings.sub_genre_err_delete"), gr.update()

                def on_style_select(name):
                    if name:
                        desc = StyleManager.get_style_description(name)
                        return name, desc or ""
                    return "", ""

                def on_style_add(name, desc):
                    if not name.strip():
                        return t("settings.style_empty_error"), gr.update()
                    success = StyleManager.add_style(name.strip(), desc.strip())
                    if success:
                        return t("settings.style_add_success"), gr.update(choices=StyleManager.get_style_names())
                    return t("settings.style_exists_error"), gr.update()

                def on_style_update(old_name, new_name, desc):
                    if not old_name:
                        return t("settings.style_none_error"), gr.update()
                    success = StyleManager.update_style(old_name, new_name.strip(), desc.strip())
                    if success:
                        return t("settings.style_update_success"), gr.update(choices=StyleManager.get_style_names())
                    return t("settings.style_update_error"), gr.update()

                def on_style_delete(name):
                    if not name:
                        return t("settings.style_none_error"), gr.update()
                    success = StyleManager.delete_style(name)
                    if success:
                        return t("settings.style_delete_success"), gr.update(choices=StyleManager.get_style_names())
                    return t("settings.style_delete_error"), gr.update()

                def on_analyze_style(text):
                    if not text or not text.strip():
                        return "", "", "❌ Please paste some text first"
                    result = StyleManager.analyze_style(text)
                    if "error" in result:
                        return "", "", f"❌ {result['error']}"
                    return result.get("name", ""), result.get("description", ""), "✅ Analysis complete"

                def on_save_analyzed_style(name, description):
                    if not name or not name.strip():
                        return "❌ Style name is empty"
                    success = StyleManager.add_style(name.strip(), description.strip())
                    if success:
                        return f"✅ Style '{name}' saved successfully"
                    return "❌ Style name already exists or save failed"

                def on_clear_all_cache():
                    try:
                        api_client = get_api_client()
                        api_client.clear_cache()
                        clear_generation_cache()
                        return t("settings.cache_cleared"), get_cache_info()
                    except Exception as e:
                        return f"❌ {str(e)}", get_cache_info()

                # Wire genre events
                genre_select.change(fn=on_genre_select, inputs=[genre_select], outputs=[genre_name_input, genre_desc_input])
                genre_add_btn.click(fn=on_genre_add, inputs=[genre_name_input, genre_desc_input], outputs=[genre_op_status, genre_select])
                genre_update_btn.click(fn=on_genre_update, inputs=[genre_select, genre_name_input, genre_desc_input], outputs=[genre_op_status, genre_select])
                genre_delete_btn.click(fn=on_genre_delete, inputs=[genre_select], outputs=[genre_op_status, genre_select])

                # Wire sub-genre events
                sub_genre_select.change(fn=on_sub_genre_select, inputs=[sub_genre_select], outputs=[sub_genre_name_input, sub_genre_desc_input])
                sub_genre_add_btn.click(fn=on_sub_genre_add, inputs=[sub_genre_name_input, sub_genre_desc_input], outputs=[sub_genre_op_status, sub_genre_select])
                sub_genre_update_btn.click(fn=on_sub_genre_update, inputs=[sub_genre_select, sub_genre_name_input, sub_genre_desc_input], outputs=[sub_genre_op_status, sub_genre_select])
                sub_genre_delete_btn.click(fn=on_sub_genre_delete, inputs=[sub_genre_select], outputs=[sub_genre_op_status, sub_genre_select])

                # Wire style events
                style_select.change(fn=on_style_select, inputs=[style_select], outputs=[style_name_input, style_desc_input])
                style_add_btn.click(fn=on_style_add, inputs=[style_name_input, style_desc_input], outputs=[style_op_status, style_select])
                style_update_btn.click(fn=on_style_update, inputs=[style_select, style_name_input, style_desc_input], outputs=[style_op_status, style_select])
                style_delete_btn.click(fn=on_style_delete, inputs=[style_select], outputs=[style_op_status, style_select])

                # Wire analyzer events
                analyzer_btn.click(
                    fn=on_analyze_style,
                    inputs=[analyzer_text_input],
                    outputs=[analyzer_result_name, analyzer_result_desc, analyzer_status],
                )
                analyzer_save_btn.click(
                    fn=on_save_analyzed_style,
                    inputs=[analyzer_result_name, analyzer_result_desc],
                    outputs=[analyzer_status],
                )

                # Wire cache events
                refresh_cache_btn.click(fn=get_cache_info, outputs=[cache_info_display])
                clear_all_cache_btn.click(fn=on_clear_all_cache, outputs=[cache_op_status, cache_info_display])
