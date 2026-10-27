# 固定基础镜像摘要，保证每次构建一致；升级时更新这里
FROM python:3.12-slim@sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    GROK_MCP_TRANSPORT=http \
    GROK_MCP_HOST=0.0.0.0 \
    GROK_MCP_PORT=8000 \
    GROK_MCP_SHOW_BANNER=false

WORKDIR /app

COPY pyproject.toml README.md requirements.lock ./
COPY src ./src

# 先按锁定版本装依赖，再装本项目（不再解析依赖），保证构建可复现
RUN pip install "pip==25.3" \
    && pip install -r requirements.lock \
    && pip install --no-deps . \
    && useradd --create-home --uid 10001 app
USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import os,urllib.request;urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\",\"8000\")}/health',timeout=3)" || exit 1

# 用 exec 形式：PID 1 是 sh，sh 再 exec 成 python，python 就能直接收到 docker stop 的 SIGTERM 并优雅退出
# （之前的 shell 形式会多套一层 /bin/sh，信号到不了 python，15 秒后被强制杀掉）
CMD ["sh", "-c", "GROK_MCP_PORT=${PORT:-8000} exec python -m grok_search.server"]
