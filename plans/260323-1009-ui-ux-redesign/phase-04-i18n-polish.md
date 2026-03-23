# Phase 4: i18n Cleanup + Final Polish

## Priority: Low | Status: Completed

## Overview
Fix all hardcoded Vietnamese strings across UI files. Remove unused i18n keys from deleted tabs. Final visual polish pass.

## Related Files
- **Modify:** `locales/VI/messages.json`, `locales/EN/messages.json`, `ui/settings_tab.py`, `ui/continue_tab.py`, `ui/projects_tab.py`

## Implementation Steps

### 4.1 Fix Hardcoded Vietnamese Strings
Found in settings_tab.py:
- Line 62: `"Thay đổi cấu hình"` → `t("settings.edit_config_header")`
- Line 69: `"Chọn cấu hình để chỉnh sửa (bỏ trống để thêm mới)"` → `t("settings.select_backend_edit")`
- Line 73: `"Chọn"` → `t("settings.select_btn")`
- Line 100: `"Cập nhật thay đổi"` → `t("settings.update_btn")`
- Line 411: `"Quản lý phong cách viết"` → `t("settings.tab_styles")`
- Line 414: `"Quản lý danh sách..."` → `t("settings.styles_desc")`
- Line 417-431: Multiple hardcoded labels → use `t()` calls
- Lines 441-464: All status messages → use `t()` calls

Found in continue_tab.py:
- Line 19: `"📂 1. Quản lý dự án"` → `t("continue_tab.project_management")`
- Line 35: `"⚙️ 2. Thông tin & Cài đặt"` → `t("continue_tab.info_settings")`
- Line 43: `"Chưa tải dự án..."` → `t("continue_tab.no_project_loaded_value")`
- Line 48: `"Cách nhớ ngữ cảnh"`, `"Toàn văn"`, `"Tóm tắt"` → i18n keys
- Line 49: `"Số chương ghi nhớ"` → i18n key

Found in rewrite_tab.py (before merge):
- Line 37: `"Bật chế độ Tự kiểm duyệt"` → i18n key
- Line 41: `"Dán nội dung cần viết lại..."` → i18n key

Found in polish_tab.py (before merge):
- Line 29: `"Bật chế độ Tự kiểm duyệt (Self-Reflection)"` → i18n key
- Line 41: placeholder → i18n key

Found in settings_tab.py cache section:
- Line 272: `"### Thống kê bộ nhớ đệm\n..."` → i18n template
- Line 287: `"✅ Đã xóa tất cả bộ nhớ đệm"` → `t("settings.cache_cleared")`

### 4.2 Add New i18n Keys
Add to both `VI/messages.json` and `EN/messages.json`:

**New keys needed:**
- `settings.edit_config_header`
- `settings.select_backend_edit`
- `settings.select_btn`
- `settings.update_btn`
- `settings.tab_styles`
- `settings.styles_desc`
- `settings.style_name`, `settings.style_desc`, `settings.style_add_btn`, etc.
- `settings.preset_creative`, `settings.preset_balanced`, `settings.preset_precise`
- `settings.generation_preset`
- `settings.cache_cleared`
- `continue_tab.text_tools`, `continue_tab.tool_mode`, `continue_tab.run_tool`
- `continue_tab.self_reflection`
- `continue_tab.project_management`, `continue_tab.info_settings`

### 4.3 Remove Unused i18n Keys
After tab deletion, remove keys for:
- `tabs.rewrite`, `tabs.polish`, `tabs.export` — these tabs no longer exist as top-level
- Keep the content keys (rewrite.header, polish.header) as they're reused in the merged UI

### 4.4 Dashboard HTML Cleanup
Ensure `_build_dashboard_html()` in projects_tab.py uses CSS classes instead of inline styles for colors (from Phase 1 changes).

### 4.5 Final Visual Polish
- Verify all tabs look consistent with warm theme
- Check `.novel-text` class applied to all generated content textboxes
- Verify tab underline color is warm gold
- Check button hierarchy (primary=gold, secondary=outline, danger=red)
- Ensure no orphan `!important` rules fighting Gradio defaults

## Todo
- [x] Audit all .py files for hardcoded Vietnamese strings
- [x] Add new i18n keys to VI/messages.json
- [x] Add new i18n keys to EN/messages.json
- [x] Replace hardcoded strings with t() calls
- [x] Remove unused i18n keys for deleted tabs
- [x] Final visual test across all 4 tabs
- [x] Verify serif font on generated novel text

## Success Criteria
- Zero hardcoded user-facing strings in .py files
- Both locale files have matching key sets
- All UI text renders correctly in both VI and EN
