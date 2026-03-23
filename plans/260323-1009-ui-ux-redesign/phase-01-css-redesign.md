# Phase 1: CSS Redesign + Header/Footer

## Priority: High | Status: Completed

## Overview
Replace current indigo/glassmorphic theme with warm neutral "book" palette. Remove dark mode entirely. Clean inline styles from app.py.

## Related Files
- **Modify:** `custom.css`, `app.py`
- **Delete:** nothing
- **Reference:** `ui/projects_tab.py` (dashboard HTML has hardcoded colors)

## Implementation Steps

### 1.1 Rewrite `custom.css` — Design Tokens
Replace all CSS with warm book theme:

```css
/* Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&family=Noto+Serif:wght@400;500;600;700&display=swap');

:root {
  --color-bg: #FEFCF9;
  --color-surface: #FFFFFF;
  --color-primary: #D4A574;
  --color-primary-hover: #C4956A;
  --color-accent: #8B6914;
  --color-text: #2D2A24;
  --color-text-muted: #8A8478;
  --color-border: #E8E0D4;
  --color-input-bg: #FAF8F5;
  --color-danger: #C44D3D;
  --color-success: #5B8A72;

  --space-xs: 4px;  --space-sm: 8px;  --space-md: 16px;
  --space-lg: 24px;  --space-xl: 32px;  --space-2xl: 48px;

  --font-body: 'Inter', system-ui, sans-serif;
  --font-heading: 'Outfit', sans-serif;
  --font-reading: 'Noto Serif', Georgia, serif;

  --radius-sm: 6px;  --radius-md: 10px;  --radius-lg: 14px;
  --shadow-sm: 0 1px 3px rgba(45,42,36,0.06);
  --shadow-md: 0 4px 12px rgba(45,42,36,0.08);
}
```

### 1.2 Remove from CSS
- All `.dark-mode` selectors and rules
- `backdrop-filter: blur()` everywhere
- `.gr-group:hover { transform: translateY(-2px) }`
- `@keyframes fadeIn` and animation on `.gradio-container`
- Gradient on `.main-title h1`

### 1.3 Update CSS Rules
- `body` → `background: var(--color-bg)`, `color: var(--color-text)`, `font-family: var(--font-body)`
- `h1,h2,h3` → `font-family: var(--font-heading)`, `color: var(--color-text)`
- `.gr-group, .gr-box, .gr-form` → `background: var(--color-surface)`, `border: 1px solid var(--color-border)`, `box-shadow: var(--shadow-sm)`, `border-radius: var(--radius-lg)`, NO blur, NO hover transform
- Tab nav → `button.selected { color: var(--color-accent); border-bottom: 2px solid var(--color-accent) }`
- Primary buttons → `background: var(--color-primary)`, `color: white`, hover: `background: var(--color-primary-hover)`
- Stop buttons → `background: var(--color-danger)`
- Inputs → `background: var(--color-input-bg)`, `border-color: var(--color-border)`, focus: `border-color: var(--color-primary)`
- Add `.novel-text` class → `font-family: var(--font-reading); line-height: 1.8; font-size: 1.05rem` (for generated content textboxes)

### 1.4 Clean `app.py` Header
**Before:**
```python
gr.Markdown(f"""
<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); ...">
    <h1 style="color: white; ...">🚀 {t("app.title")}</h1>
```

**After:**
```python
gr.Markdown(f"""
<div class="app-header">
    <h1 class="app-title">{t("app.title")}</h1>
    <p class="app-subtitle">{t("app.subtitle")}</p>
</div>
""")
```

Add CSS:
```css
.app-header { text-align: center; padding: var(--space-xl) 0 var(--space-lg); }
.app-title { font-size: 2.2rem; color: var(--color-accent); margin: 0; }
.app-subtitle { color: var(--color-text-muted); font-size: 1rem; margin-top: var(--space-xs); }
```

### 1.5 Clean `app.py` Footer
Replace inline styles with CSS class:
```python
gr.Markdown("""
<div class="app-footer">
    <p>TiniX Story v1.0.0</p>
    <p class="footer-credit">Made with care by TiniX AI</p>
</div>
""")
```

### 1.6 Remove Dark Mode JS Injection
Delete lines 63-71 in `app.py` (theme_js variable and dark mode script injection).

### 1.7 Update Dashboard HTML Colors
In `projects_tab.py` `_build_dashboard_html()`:
- Replace `#1f2937` (dark header) → use CSS class instead
- Replace `#4caf50` (green bar) → `var(--color-success)`
- Replace `#e0e0e0` (gray bar bg) → `var(--color-border)`

## Todo
- [x] Rewrite CSS tokens + body/heading styles
- [x] Remove dark mode, blur, hover lifts, fadeIn
- [x] Update card/button/input/tab styles
- [x] Add `.novel-text` and `.app-header`/`.app-footer` classes
- [x] Clean app.py header (remove inline styles + emoji)
- [x] Clean app.py footer
- [x] Remove dark mode JS injection from app.py
- [x] Update dashboard HTML hardcoded colors
- [x] Visual test: verify all tabs render correctly

## Success Criteria
- Zero inline `style=` in app.py header/footer
- All colors reference CSS vars
- No dark mode code anywhere
- Clean, warm, book-like appearance
