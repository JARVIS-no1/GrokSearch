FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip && pip install .

CMD sh -c "fastmcp run src/grok_search/server.py --transport http --host 0.0.0.0 --port ${PORT:-8000} --path /mcp/"
