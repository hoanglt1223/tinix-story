# TiniX Story 1.0

**TiniX Story 1.0** is a production-ready, highly sophisticated intelligent novel generation system. It provides a comprehensive suite of AI-powered tools designed to assist authors, writers, and creators in brainstorming, outlining, drafting, rewriting, and polishing long-form fiction.

## 📖 Documentation / Tài liệu

| Language | Link |
|----------|------|
| 🇬🇧 English (Default) | See below for English instructions |
| 🇻🇳 Tiếng Việt (Vietnamese) | [locales/VI/huong_dan_su_dung.md](locales/VI/huong_dan_su_dung.md) |

---

## 🌟 Core Features

- **✍️ Smart Creation**: Write novels from scratch. Generate creative titles, build detailed character profiles, design world settings, and construct comprehensive outlines automatically before generating chapters.
- **⏸️ Resume Capability & Auto-Save**: Fully supports pausing generation. Every chapter is saved automatically. You can resume writing from exactly where you left off via Project Management.
- **🔄 Smart Rewrite**: Upload your existing text and rewrite it using 17 high-quality, preset styles (e.g., Eastern Fantasy, Hard Sci-Fi, Urban Romance, Horror, etc.).
- **📖 Smart Continue**: Upload a partially written novel. The AI will analyze the context, characters, and world-building, and automatically continue the story maintaining your style and tone.
- **✨ Novel Polish**: Advanced polishing tools with 8 specific modes: General Polish, Find Errors, Improvement Suggestions, Direct Edit, Remove AI Tone, Enhance Details, Optimize Dialogue, and Improve Pacing.
- **📄 Flexible File Parsing**: Upload your own files (`.txt`, `.pdf`, `.epub`, `.md`, `.docx`). The system supports multiple parsing mechanisms including auto-split, split by word count, and split by custom Regex patterns.
- **💾 Multi-Format Export**: Export your completed or in-progress projects into Word (`.docx`), Plain Text (`.txt`), Markdown (`.md`), or HTML (`.html`) with a single click.
- **📂 Project Management**: Manage multiple novel projects simultaneously. Track completion percentage, chapter counts, update dates, and manage generation cache.
- **⚙️ Flexible Configuration (Multi-API)**: Add multiple API backends (OpenAI compatible, Anthropic, Google, Ollama). Set default providers, test connections, and configure individual generation parameters (Temperature, Top P, Max Tokens) per backend.
- **🛡️ Built-in Resilience**:
  - **Error Retry**: Automatically retries if a generated chapter fails or returns 0 words.
  - **Port Auto-detection**: Automatically finds available ports if the default Gradio port (7860) is occupied.
  - **Rate Limiting Handling**: Built-in token bucket algorithms to gracefully handle API rate limits.

---

## 🔧 Technology Stack & Architecture

- **Backend**: Python 3.11+, leveraging async operations and thread-safe concurrency.
- **Frontend**: Gradio 4.0+ for a responsive, component-driven Web UI.
- **Persistence**: SQLite for robust project metadata storage, combined with standard file I/O for chapter content and caching.
- **Caching**: Intelligent caching system stores generated chapters and context summaries to drastically reduce redundant API calls and save costs.
- **Internationalization (i18n)**: Fully dynamic string loading supporting multiple locales dynamically switchable via environment variables.

---

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8 or higher installed on your system.
- Git (optional, for cloning the repository).

### Installation & Setup

1. **Clone or download the repository:**

   ```bash
   git clone https://github.com/tinix-ai/tinix-story.git
   cd tinix-story
   ```

2. **Create a virtual environment (Recommended):**

   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   *(Optional) To enable PDF or EPUB parsing:*

   ```bash
   pip install PyMuPDF ebooklib beautifulsoup4
   ```

4. **Launch the Application:**

   ```bash
   python app.py
   ```

   The terminal will display the local URL (usually `http://127.0.0.1:7860`). Open this link in your browser.

---

## 🌐 i18n (Internationalization)

The application supports multiple languages out of the box. Language files are stored in the `locales/` directory:

```text
locales/
├── i18n.py               # i18n helper module
├── __init__.py           
├── EN/                   # English (Default fallback)
│   └── messages.json     
└── VI/                   # Vietnamese
    ├── messages.json     
    └── huong_dan_su_dung.md         
```

### Switching Language

Set the `APP_LANGUAGE` environment variable before starting the app.

**Windows (Command Prompt):**

```cmd
set APP_LANGUAGE=VI
python app.py
```

**Windows (PowerShell):**

```powershell
$env:APP_LANGUAGE="VI"
python app.py
```

**macOS/Linux:**

```bash
APP_LANGUAGE=VI python app.py
```

---

## 💻 Contribution & Support

We welcome pull requests and issue reports! If you encounter connection issues, ensure your API keys are valid and double check the logs located in the `logs/` directory.

### License

This project is licensed under the **MIT License**.
