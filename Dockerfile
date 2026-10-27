FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    GROK_MCP_TRANSPORT=http \
    GROK_MCP_HOST=0.0.0.0 \
    GROK_MCP_PORT=8000 \
    GROK_MCP_SHOW_BANNER=false

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip && pip install . \
    && useradd --create-home --uid 10001 app
USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import os,urllib.request;urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\",\"8000\")}/health',timeout=3)" || exit 1

CMD sh -c "GROK_MCP_PORT=${PORT:-8000} python -m grok_search.server"
