# 多架构 Dockerfile：python:slim 官方镜像同时提供 amd64 / arm64 manifest，
# 配合 docker buildx 即可一次构建 linux/amd64 与 linux/arm64。
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 先装依赖，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制应用代码
COPY app ./app

# 运行时以非 root 用户运行
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/voices', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
