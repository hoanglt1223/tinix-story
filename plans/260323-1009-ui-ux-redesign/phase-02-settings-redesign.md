# Phase 2: Settings Smart Defaults + Presets

## Priority: High | Status: Completed

## Overview
Simplify settings from 8 sub-tabs → 3 sub-tabs. Add API key auto-detection. Replace 8 generation param sliders with 3 presets + expandable custom. Merge genre/sub-genre/style into "Content Library" accordion.

## Related Files
- **Modify:** `ui/settings_tab.py`, `core/config.py` (add detection helper)
- **Reference:** `core/config_api.py`, `services/style_manager.py`, `services/genre_manager.py`

## Architecture

### Current Settings Structure (8 sub-tabs)
1. API Backends — 8 form fields + CRUD
2. Generation Params — 8 sliders/dropdowns
3. Cache Management
4. Genre Management — CRUD
5. Sub-genre Management — CRUD
6. Writing Styles — CRUD
7. AI Style Analyzer
8. Theme (Light/Dark) — **REMOVE** (dark mode dropped)
9. Cost Tracker

### New Settings Structure (3 sub-tabs)
1. **API Backends** — smart key detection + simplified form
2. **Generation** — 3 presets + expandable custom + cost tracker
3. **Content Library** — genre/sub-genre/style in accordions + style analyzer + cache

## Implementation Steps

### 2.1 API Key Auto-Detection
Add helper function to `core/config.py` or new `utils/api_key_detector.py`:

```python
def detect_provider_from_key(api_key: str) -> dict | None:
    """Return provider info dict or None if unrecognized."""
    key = api_key.strip()
    if key.startswith("sk-ant-"):
        return {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "name": "Anthropic"}
    if key.startswith("sk-") and not key.startswith("sk-ant-"):
        return {"provider": "openai", "model": "gpt-4o", "name": "OpenAI"}
    if key.startswith("gsk_"):
        return {"provider": "groq", "model": "llama3-70b-8192", "name": "Groq"}
    if key.startswith("xai-"):
        return {"provider": "xai", "model": "grok-2", "name": "xAI"}
    if len(key) == 39 and key.startswith("AI"):
        return {"provider": "google", "model": "gemini-2.0-flash", "name": "Google"}
    # Add more heuristics as needed
    return None  # Show manual provider dropdown
```

### 2.2 Simplified Backend Form
**Quick Setup mode (default):**
```
API Key: [_________________________]
↳ Auto-detected: OpenAI (gpt-4o)     ← shown after typing
[Save Backend]

▸ Advanced (click to expand)
  - Name, Provider, Base URL, Model, Type, Timeout
```

**Implementation:**
- Single `gr.Textbox` for API key with `.change()` handler calling `detect_provider_from_key()`
- Show detection result as `gr.Markdown` below
- `gr.Accordion("Advanced", open=False)` wrapping existing form fields
- On save: if auto-detected, auto-fill provider/url/model/name; else require manual

### 2.3 Generation Presets
Replace 8 simultaneous sliders with preset radio + expandable:

```python
preset_radio = gr.Radio(
    choices=[t("settings.preset_creative"), t("settings.preset_balanced"), t("settings.preset_precise")],
    value=t("settings.preset_balanced"),
    label=t("settings.generation_preset")
)

PRESETS = {
    "creative": {"temperature": 1.2, "top_p": 0.95, "max_tokens": 16000, "chapter_target_words": 3000},
    "balanced": {"temperature": 0.8, "top_p": 0.9, "max_tokens": 8000, "chapter_target_words": 2000},
    "precise":  {"temperature": 0.5, "top_p": 0.8, "max_tokens": 4000, "chapter_target_words": 1500},
}
```

- Preset click → auto-fills AND saves to config
- `gr.Accordion("Custom Parameters", open=False)` wrapping sliders for manual override
- Keep writing_style, tone, char_dev, plot_complexity in the custom section

### 2.4 Merge Content Library
Single sub-tab with 3 `gr.Accordion` sections:
1. Genre Management (existing CRUD)
2. Sub-genre Management (existing CRUD)
3. Writing Styles (existing CRUD + AI analyzer below)

Move cache management here too as 4th accordion (it's a utility, not a primary setting).

### 2.5 Remove Theme Sub-tab
Delete the entire Theme sub-tab code (lines 512-552 in settings_tab.py). No dark mode = no toggle needed.

### 2.6 Relocate Cost Tracker
Move cost tracker from settings into the Generation sub-tab as a collapsible section at bottom. Cost is contextually related to generation, not a standalone setting.

## Todo
- [x] Create `utils/api_key_detector.py` with `detect_provider_from_key()`
- [x] Rewrite backend form: quick key input + auto-detect + advanced accordion
- [x] Add generation presets (Creative/Balanced/Precise)
- [x] Wrap existing param sliders in "Custom" accordion
- [x] Merge genre/sub-genre/style into Content Library tab with accordions
- [x] Move style analyzer into Writing Styles accordion
- [x] Move cache into Content Library tab
- [x] Remove Theme sub-tab entirely
- [x] Move cost tracker under Generation tab
- [x] Test: add backend via quick setup (paste key → auto-detect → save)
- [x] Test: preset selection applies correct params

## Success Criteria
- New user can add backend by pasting just an API key (for known providers)
- Settings reduced from 8 → 3 sub-tabs
- Generation presets work with one click
- All existing functionality preserved (no data loss)

## Risks
- API key format collisions between providers → always show "Override" link
- Existing backends in DB won't have detection applied → only affects new additions
