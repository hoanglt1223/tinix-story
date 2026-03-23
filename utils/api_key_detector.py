def detect_provider_from_key(api_key: str) -> dict | None:
    """Return provider info dict or None if unrecognized."""
    key = api_key.strip()
    if not key:
        return None
    if key.startswith("sk-ant-"):
        return {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "name": "Anthropic", "base_url": "https://api.anthropic.com/v1"}
    if key.startswith("sk-") and not key.startswith("sk-ant-"):
        return {"provider": "openai", "model": "gpt-4o", "name": "OpenAI", "base_url": "https://api.openai.com/v1"}
    if key.startswith("gsk_"):
        return {"provider": "groq", "model": "llama3-70b-8192", "name": "Groq", "base_url": "https://api.groq.com/openai/v1"}
    if key.startswith("xai-"):
        return {"provider": "xai", "model": "grok-2", "name": "xAI", "base_url": "https://api.x.ai/v1"}
    if key.startswith("AI") and len(key) >= 35:
        return {"provider": "google", "model": "gemini-2.0-flash", "name": "Google", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai"}
    return None
