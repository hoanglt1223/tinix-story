# Code Review: UI/UX Redesign — "Warm Book" Theme

**Date:** 2026-03-23
**Reviewer:** code-reviewer
**Score: 7/10**

---

## Scope

- **Files reviewed:** 9 (app.py, custom.css, settings_tab.py, continue_tab.py, text_tools.py, projects_tab.py, api_key_detector.py, EN/messages.json, VI/messages.json)
- **Deleted files verified:** 3 (rewrite_tab.py, polish_tab.py, export_tab.py)
- **Focus:** Functionality preservation, broken imports, CSS variables, i18n, security

## Overall Assessment

Solid tab consolidation. All event handlers from deleted tabs are present in new locations (text_tools.py, projects_tab.py). No broken imports to deleted modules. CSS uses variables correctly. However, significant hardcoded Vietnamese strings remain across all UI files, and two security concerns with API key handling need attention.

---

## Critical Issues

### C1. API key fields use `type="text"` instead of `type="password"`
**File:** `ui/settings_tab.py` lines 66, 148
Both `quick_key_input` and `api_key_input` use `type="text"`, displaying API keys in plaintext.
```python
# Current
quick_key_input = gr.Textbox(..., type="text")
api_key_input = gr.Textbox(..., type="text")

# Fix
quick_key_input = gr.Textbox(..., type="password")
api_key_input = gr.Textbox(..., type="password")
```
**Impact:** API keys visible on screen, over-the-shoulder risk. Quick-detect on change still works with password type.

### C2. `on_quick_detect` fires on every keystroke via `.change()` event
**File:** `ui/settings_tab.py` line 267
```python
quick_key_input.change(fn=on_quick_detect, inputs=[quick_key_input], outputs=[quick_detect_result])
```
The `detect_provider_from_key` function is lightweight (prefix matching), so no performance issue, BUT it displays partial key info ("Detected: OpenAI") while user is still typing, which could leak provider info. If using `type="password"`, the detect result reveals what the masked field contains.

**Recommendation:** Remove the `.change()` auto-detect. Keep only the button-click flow, or add a separate "Detect" button.

---

## Warnings (High Priority)

### W1. Extensive hardcoded Vietnamese strings in UI files
Multiple files contain user-facing Vietnamese strings not routed through `t()`:

| File | Examples |
|------|----------|
| `text_tools.py:99,107,122` | `"Dang goi AI xu ly... Vui long cho."` |
| `settings_tab.py:204,210,221` | `"Vui long nhap ten giao dien"`, `"Dang kiem tra ket noi API"` |
| `settings_tab.py:560,563` | Placeholder text `"Vi du: Muot ma tu nhien..."` |
| `settings_tab.py:600` | `"Thong ke bo nho dem"` |
| `continue_tab.py:137-145` | `"The loai:"`, `"Nhan vat:"`, `"The gioi / Boi canh:"` |
| `continue_tab.py:250,390,399,418,430...` | Dozens of status messages, labels |
| `create_tab.py:23,44,57,71...` | Accordion labels, radio choices, all hardcoded |
| `projects_tab.py:299,429` | `"Dang xem phien ban"`, `"Chuong {ch.num}"` |

**Impact:** English UI mode (`APP_LANGUAGE=EN`) shows Vietnamese strings.
**Recommendation:** Batch-add i18n keys for all status/progress messages. Priority: `text_tools.py` and `settings_tab.py` (newly created/modified files should be clean).

### W2. Project dropdowns in projects_tab not synced on dashboard refresh
**File:** `ui/projects_tab.py` line 641
`refresh_dashboard_btn` only updates `dashboard_html` and `delete_project_selector`. The `editor_project_selector`, `export_project_selector`, `consistency_project_selector`, and `archive_project_selector` dropdowns remain stale.

**Fix:** Either refresh all 5 dropdowns from `on_refresh_projects`, or add individual refresh buttons per section (export already has one at line 380).

### W3. `api_key_detector.py` — `sk-` prefix collision with non-OpenAI providers
**File:** `utils/api_key_detector.py` line 8
```python
if key.startswith("sk-") and not key.startswith("sk-ant-"):
    return {"provider": "openai", ...}
```
Several OpenAI-compatible providers (e.g., Mistral, Together AI, Fireworks) also issue `sk-` prefixed keys. Auto-detecting as OpenAI and setting `base_url` to `api.openai.com` will silently fail for those providers.

**Recommendation:** Add a comment warning about this limitation, and show a note in the UI: "Detected as OpenAI. If using another provider, use Advanced config."

### W4. `create_tab.py` not part of redesign but heavily hardcoded
Not modified in this PR but `create_tab.py` has the most hardcoded Vietnamese strings of any file (accordion labels, radio choices, status messages). Since the other 3 tabs were cleaned up, this creates an inconsistent experience.

---

## Medium Priority

### M1. `text_tools.py` — no error handling when generator is None
**File:** `ui/text_tools.py` line 97
```python
gen = app_state.get_generator()
```
If no backend is configured, `get_generator()` may raise or return an object that fails on `.rewrite_paragraph()`. The old `rewrite_tab.py` had the same issue, so this is a pre-existing problem, but the consolidation was an opportunity to add a guard:
```python
gen = app_state.get_generator()
if gen is None:
    yield t("app.no_backends_warning"), gr.update(), gr.update(interactive=True)
    return
```

### M2. Export section hardcodes `"Chuong"` in chapter headers
**File:** `ui/projects_tab.py` line 429
```python
full_text += f"## Chuong {ch.num}: {ch.title}\n\n"
```
Should use `t()` for the chapter prefix to support English export output.

### M3. CSS — `custom.css` injected via `gr.HTML` with `visible=False`
**File:** `app.py` line 65
```python
gr.HTML(f"<style>{custom_css}</style>", visible=False)
```
Gradio's `visible=False` may or may not render the HTML to DOM depending on version. Safer approach: use Gradio's `css` parameter directly:
```python
with gr.Blocks(title=t("app.title"), css=custom_css) as app:
```
This is the canonical Gradio approach and avoids the `visible=False` ambiguity.

### M4. `settings_tab.py` line 113 — `ConfigAPIManager.list_backends()` called at build time
```python
manage_backend_select = gr.Dropdown(
    choices=[b['name'] for b in ConfigAPIManager.list_backends().get("data", [])],
```
This DB call happens at import/build time. Recent commit `e004316` was specifically about eliminating build-time DB calls. This is a regression of that fix.

**Fix:** Initialize with empty choices, populate via `.load()` event or the existing refresh button.

---

## Low Priority

### L1. `custom.css` — `color: white` on line 125
Hardcoded color instead of CSS variable. Minor since white-on-primary is a deliberate design choice, but for consistency could use `--color-bg` or define `--color-on-primary`.

### L2. Version entry parsing is fragile
**File:** `ui/projects_tab.py` line 294
```python
ver_num = int(version_entry.split("--")[0].replace("v", "").strip())
```
Depends on the exact format of `t("version.version_entry")`. If the i18n template changes, parsing breaks silently. Consider storing version number in a `gr.State` instead.

---

## Positive Observations

- **Clean tab consolidation**: 7 tabs -> 4 tabs, all event handlers properly migrated
- **CSS variable system**: Well-structured with semantic naming, good spacing/typography tokens
- **Quick-add API flow**: Good UX improvement with `detect_provider_from_key`
- **Accordion-based organization**: Reduces visual clutter while keeping all functionality accessible
- **i18n keys added**: ~60 new keys in both EN and VI for the new UI elements
- **No broken imports**: Verified zero references to deleted modules remain in codebase

---

## Metrics

| Metric | Value |
|--------|-------|
| Syntax errors | 0 |
| Broken imports | 0 |
| Hardcoded Vietnamese strings (UI files) | ~80+ instances |
| CSS hardcoded colors | 1 minor (`white`) |
| New i18n keys | ~60 per locale |
| Security issues | 2 (API key exposure) |

---

## Recommended Actions (Priority Order)

1. **[Critical]** Change API key inputs to `type="password"` and remove auto-detect on change
2. **[High]** Add i18n keys for all hardcoded Vietnamese strings in `text_tools.py` and `settings_tab.py`
3. **[High]** Fix build-time DB call in `settings_tab.py` line 113 (regression of e004316)
4. **[Medium]** Add null-guard for generator in `text_tools.py`
5. **[Medium]** Use `gr.Blocks(css=...)` instead of `gr.HTML` injection
6. **[Medium]** Sync all project dropdowns on dashboard refresh
7. **[Low]** Add disclaimer to quick-detect about `sk-` prefix ambiguity

---

## Unresolved Questions

1. Was `create_tab.py` intentionally left out of the i18n cleanup? It has the most hardcoded strings.
2. The `on_quick_detect` auto-fires on `.change()` — is this intended UX, or should it be button-triggered only?
3. Should the version entry format be decoupled from i18n templates to avoid fragile parsing?
