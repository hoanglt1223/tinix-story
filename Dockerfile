# Dockerfile cho TiniX Story 1.0
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Dependencies hệ thống
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt dependencies Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tạo các thư mục cần thiết
RUN mkdir -p logs data

# Sao chép mã nguồn
COPY . .

# Expose port (Gradio default)
EXPOSE 7860

# Biến môi trường mặc định
ENV NOVEL_TOOL_HOST=0.0.0.0
ENV NOVEL_TOOL_PORT=7860
# Turso (để trống = dùng SQLite local)
ENV TURSO_DATABASE_URL=""
ENV TURSO_AUTH_TOKEN=""

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

CMD ["python", "app.py"]
