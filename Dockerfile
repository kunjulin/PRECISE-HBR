# 使用官方 Python 3.11 slim 映像作為基礎
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 創建非 root 使用者
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 複製應用程式代碼
COPY --chown=app:app . .

# 創建必要的目錄
RUN mkdir -p logs static/images templates

# 設定環境變數
ENV FLASK_APP=APP.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 使用 Gunicorn 運行應用程式
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "APP:app"] 