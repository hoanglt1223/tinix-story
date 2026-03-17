# Dockerfile cho công cụ sáng tác tiểu thuyết AI
# Dựa trên image chính thức của Python 3.11
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Thiết lập biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Cài đặt các dependencies hệ thống
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Sao chép tệp dependencies
COPY requirements.txt .
COPY requirements-dev.txt .

# Cài đặt dependencies Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Tạo các thư mục cần thiết
RUN mkdir -p logs cache output data backups templates project_templates plugins

# Sao chép mã nguồn ứng dụng
COPY . .

# Thiết lập quyền truy cập
RUN chmod +x start.sh start.bat run.py

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Lệnh khởi động
CMD ["python", "run.py"]