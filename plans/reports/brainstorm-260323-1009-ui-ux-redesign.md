# Brainstorm: TiniX Story UI/UX Redesign

## Problem Statement

TiniX Story has visual inconsistencies across tabs (inline styles vs CSS vars, hardcoded colors, mixed i18n), settings overload (5 sub-tabs, 20+ fields), and lacks a cohesive design system. Goal: clean reading-focused layout, warm light-only theme, smart defaults to reduce manual config.

## Decisions Made

- **Drop dark mode** entirely — focus 100% on polished light theme
- **Warm neutral palette** — book-like, cream/gold tones inspired by tangthuvien reading experience
- **Smart defaults** — auto-detect provider from API key, minimal fields shown
- **Fix visual inconsistency** — unified design tokens, no inline styles
- **Tech approach** — whatever works best (CSS + JS + Gradio components)

---

## Current Issues Found

### 1. Visual Inconsistency
- `app.py` header: inline `#667eea/#764ba2` gradient — doesn't match CSS vars `#6366f1`
- Footer: hardcoded `#e0e0e0`, `#666`, `#999` — no CSS vars
- Settings tab: hardcoded Vietnamese strings outside i18n (lines 62, 69, 73)
- No consistent spacing/sizing system — each tab does its own thing
- Emoji usage inconsistent (some tabs use them, some don't)

### 2. Settings Overload
- 5 sub-tabs with 20+ event handlers
- Backend form shows ALL 8 fields at once (name, provider, type, URL, key, model, timeout)
- Generation params: 8 sliders/dropdowns simultaneously visible
- Genre/sub-genre/style management = 3 identical CRUD patterns

### 3. CSS Architecture
- Good: CSS vars exist, card/button styles defined
- Bad: `.dark-mode` class takes up ~30% of CSS — dead code after removal
- Bad: hover lift (`translateY(-2px)`) on `.gr-group` is distracting for content-focused UI
- Bad: glassmorphic `backdrop-filter: blur(12px)` — heavy for no real purpose

---

## Recommended Solution

### A. Design System — "Warm Book" Theme

**Color Tokens:**
```css
:root {
  /* Primary palette */
  --color-bg:        #FEFCF9;     /* warm white page */
  --color-surface:   #FFFFFF;     /* cards */
  --color-primary:   #D4A574;     /* warm gold */
  --color-primary-hover: #C4956A;
  --color-accent:    #8B6914;     /* deep gold for emphasis */
  --color-text:      #2D2A24;     /* warm black */
  --color-text-muted:#8A8478;     /* secondary text */
  --color-border:    #E8E0D4;     /* warm gray borders */
  --color-input-bg:  #FAF8F5;     /* slightly warm input bg */
  --color-danger:    #C44D3D;     /* warm red for destructive */
  --color-success:   #5B8A72;     /* sage green for success */

  /* Spacing scale (4px base) */
  --space-xs: 4px;  --space-sm: 8px;  --space-md: 16px;
  --space-lg: 24px; --space-xl: 32px; --space-2xl: 48px;

  /* Typography */
  --font-body: 'Inter', system-ui, sans-serif;
  --font-heading: 'Outfit', sans-serif;
  --font-reading: 'Noto Serif', Georgia, serif;  /* NEW: for generated content */

  /* Radius */
  --radius-sm: 6px;  --radius-md: 10px;  --radius-lg: 14px;

  /* Shadows — subtle, warm */
  --shadow-sm: 0 1px 3px rgba(45,42,36,0.06);
  --shadow-md: 0 4px 12px rgba(45,42,36,0.08);
}
```

**Key Design Principles:**
1. **No hover lift animations** — content stays grounded, professional
2. **No glassmorphism/blur** — clean solid surfaces, warm white
3. **Serif font for generated novel text** — book-like reading experience
4. **Flat, warm cards** — subtle shadow only, no border tricks
5. **Consistent 8px grid** — all spacing multiples of 8
6. **Tab underline in warm gold** — not gradient, just solid accent

### B. Layout Restructure — "Reading-First"

**Header:** Simplified, no gradient background. Clean logo + subtitle on warm bg. Remove emoji from title.

```
┌─────────────────────────────────────────┐
│           TiniX Story                    │
│    Công cụ sáng tác tiểu thuyết AI      │
│  [Create] [Continue] [Projects] [⚙]     │
└─────────────────────────────────────────┘
```

**Tab consolidation (7 → 4 tabs):**
1. **Sáng tác** (Create) — unchanged core
2. **Tiếp tục** (Continue) — absorb Rewrite + Polish as sub-actions on selected chapter (dropdown: "Tiếp tục / Viết lại / Đánh bóng")
3. **Dự án** (Projects) — absorb Export as action buttons per project
4. **⚙ Cài đặt** (Settings icon only) — simplified

**Rationale:** Rewrite and Polish are tiny (68 and 63 lines). They're just variations of "process chapter text" — no need for separate tabs. Export is a project action, not a standalone workflow.

### C. Settings Redesign — "Smart Defaults"

**Current:** 5 sub-tabs, all fields visible
**Proposed:** 2 modes, smart detection

#### Smart Backend Setup
```
┌─────────────────────────────────────────┐
│  Quick Setup                             │
│                                          │
│  API Key: [________________________________]
│  ↳ Auto-detected: OpenAI (gpt-4o)      │
│                                          │
│  [+ Add another backend]                │
│                                          │
│  ▸ Advanced Settings                    │
└─────────────────────────────────────────┘
```

**Auto-detection logic:**
- `sk-` prefix → OpenAI, default model `gpt-4o`
- `sk-ant-` prefix → Anthropic, default `claude-sonnet-4-20250514`
- Length/format heuristics for Google, DeepSeek, Groq, etc.
- If unrecognized → show provider dropdown

**Generation params:** Replace 8 sliders with 3 presets:
- **Sáng tạo** (Creative): temp=1.2, top_p=0.95, words=3000
- **Cân bằng** (Balanced): temp=0.8, top_p=0.9, words=2000 ← default
- **Chính xác** (Precise): temp=0.5, top_p=0.8, words=1500

Click preset → auto-fills. Show "Custom" expandable for manual override.

**Collapse Genre/SubGenre/Style CRUD** into single "Content Library" sub-tab with accordion sections.

### D. CSS Cleanup Scope

**Remove:**
- All `.dark-mode` rules and JS injection
- `backdrop-filter: blur()` on all elements
- `translateY(-2px)` hover transforms on cards
- Inline styles from `app.py` header/footer
- Gradient on title (use solid warm gold)
- `@keyframes fadeIn` (unnecessary)

**Add:**
- Warm color tokens (see palette above)
- Serif font import for reading content
- Proper spacing scale
- Consistent button hierarchy (primary=gold, secondary=outline, danger=warm red)
- Clean tab underline style
- Input focus ring in warm gold

**Estimated CSS reduction:** ~200 lines → ~130 lines (remove dark mode, simplify effects)

### E. i18n Fixes

- Move all hardcoded Vietnamese strings in `settings_tab.py` to locale files
- Lines 62, 69, 73 specifically: "Thay đổi cấu hình", "Chọn cấu hình để chỉnh sửa", "Chọn"

---

## Implementation Considerations

### Effort Estimate (by area)
| Area | Files | Complexity |
|------|-------|-----------|
| CSS redesign | `custom.css` | Medium — rewrite vars, remove dark mode |
| Header/footer | `app.py` | Low — remove inline styles, use CSS classes |
| Tab consolidation | `continue_tab.py`, `rewrite_tab.py`, `polish_tab.py` | Medium — merge rewrite/polish into continue |
| Settings redesign | `settings_tab.py` | High — smart detection logic, preset system |
| Export merge | `export_tab.py`, `projects_tab.py` | Low — move export buttons to project view |
| i18n fixes | `locales/VI/messages.json`, `locales/EN/messages.json` | Low |

### Risks
1. **Tab consolidation breaking i18n keys** — need to update both locale files
2. **Smart API key detection** — false positives possible; need fallback to manual mode
3. **Gradio theme conflicts** — Gradio injects its own CSS; `!important` wars may increase
4. **User muscle memory** — existing users know 7 tabs; switching to 4 needs clear affordances

### Mitigation
- Keep all existing URL routes working (Gradio handles this)
- Smart detection should always show "Override" option
- Test CSS specificity carefully against Gradio 4.x defaults
- Add tooltips on merged tabs explaining sub-actions

---

## Success Metrics

1. **Visual consistency**: All colors from CSS vars, zero inline styles in `.py` files
2. **Settings simplification**: New user can add first backend in ≤3 fields (key only for known providers)
3. **Tab reduction**: 7 → 4 tabs, zero lost functionality
4. **Reading experience**: Generated novel text uses serif font, comfortable line-height
5. **CSS cleanliness**: No dark mode code, no `!important` where avoidable

---

## Next Steps

1. Create implementation plan with phased approach
2. Phase 1: CSS redesign + header/footer cleanup (quick wins)
3. Phase 2: Settings smart defaults + presets
4. Phase 3: Tab consolidation (continue absorbs rewrite/polish, projects absorbs export)
5. Phase 4: i18n cleanup + final polish
