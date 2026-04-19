![Image](../images/title.png)
<div align="center">

<!-- # Grok Search MCP -->

English | [简体中文](../README.md)

**Grok-with-Tavily MCP: a general-purpose web search MCP for Claude Code / Cherry Studio / Chatbox / Codex / Cursor**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0.0+-green.svg)](https://github.com/jlowin/fastmcp)

</div>

---

## 1. Overview

Grok Search MCP is an MCP server built on [FastMCP](https://github.com/jlowin/fastmcp) with a dual-engine architecture:

- **Grok** for AI-driven web search
- **Tavily** for web extraction and site mapping
- **Firecrawl** as a fallback extractor when Tavily fails

It provides a unified real-time web access layer for Claude Code, Cherry Studio, Chatbox, Codex, Cursor, and other MCP-compatible clients.

```text
LLM Client ──MCP──► Grok Search Server
                    ├─ web_search  ───► Grok API
                    ├─ web_fetch   ───► Tavily Extract → Firecrawl Scrape
                    └─ web_map     ───► Tavily Map
```

---

## 2. Multi-client / multi-transport support

This version supports three transports:

- `stdio`: best default for local clients
- `http`: Streamable HTTP for Railway / Docker / cloud deployment
- `sse`: compatibility mode for older remote clients

### Recommended order

1. Prefer **`stdio`** for local clients
2. Prefer **`http` + `/mcp/`** for standard remote deployment
3. Use **`sse` + `/sse/`** only when a remote client has poor Streamable HTTP compatibility

---

## 3. Features

- Dual-engine search: Grok + Tavily
- Firecrawl fallback when Tavily extraction fails
- OpenAI-compatible upstream API support
- Automatic time-context injection for time-sensitive queries
- Smart retries with Retry-After parsing and backoff
- Compatibility with Cherry Studio, Chatbox, Claude Code, Codex, Cursor
- Multiple transport modes: stdio / Streamable HTTP / SSE
- Windows parent-process monitoring for local stdio runs

---

## 4. Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended)
- or a working `pip`

Install uv:

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> If you hit isolation, TLS, or dependency issues on Windows, WSL is recommended.

---

## 5. Default install source

The install examples in this document currently use the following repository:

```text
git+https://github.com/JARVIS-no1/GrokSearch@main
```

If you later publish your own fork, replace it globally with your repository URL.

---

## 6. Quick start

### 1) Local stdio mode (recommended)

Best for:

- Claude Code
- Cherry Studio
- Codex / Cursor
- local Chatbox MCP

#### Run directly with uvx

```bash
uvx --from git+https://github.com/JARVIS-no1/GrokSearch@main grok-search
```

Or explicitly select stdio:

```bash
uvx --from git+https://github.com/JARVIS-no1/GrokSearch@main grok-search-stdio
```

### 2) Install locally and run

```bash
pip install .
```

Default entrypoint:

```bash
grok-search
```

Explicit entrypoints:

```bash
grok-search-stdio
grok-search-http
grok-search-sse
```

---

## 7. Remote deployment

### Default Docker / Railway mode

The current Dockerfile defaults to:

- `GROK_MCP_TRANSPORT=http`
- listen on `0.0.0.0:${PORT}`
- default path `/mcp/`
- health check path `/health`

Default remote MCP endpoint:

```text
https://your-domain.example/mcp/
```

Health check endpoint:

```text
https://your-domain.example/health
```

### If you need Chatbox compatibility

Set the deployment environment variable to:

```bash
GROK_MCP_TRANSPORT=sse
```

Then the default endpoint becomes:

```text
https://your-domain.example/sse/
```

### Railway template

This repo now includes:

- `railway.json.example`
- `docs/RAILWAY.md`

If you want to deploy on Railway, start with:

- [`docs/RAILWAY.md`](./RAILWAY.md)

---

## 8. Environment variables

### Core API config

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROK_API_URL` | Yes | - | Grok API endpoint, must be OpenAI-compatible |
| `GROK_API_KEY` | Yes | - | Grok API key |
| `GROK_MODEL` | No | `grok-4-fast` | Default model |
| `TAVILY_API_KEY` | No | - | Tavily API key |
| `TAVILY_API_URL` | No | `https://api.tavily.com` | Tavily endpoint |
| `TAVILY_ENABLED` | No | `true` | Enable Tavily |
| `FIRECRAWL_API_KEY` | No | - | Firecrawl API key |
| `FIRECRAWL_API_URL` | No | `https://api.firecrawl.dev/v2` | Firecrawl endpoint |

### MCP transport config

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROK_MCP_TRANSPORT` | No | `stdio` | `stdio` / `http` / `sse` |
| `GROK_MCP_HOST` | No | `127.0.0.1` | HTTP/SSE bind host |
| `GROK_MCP_PORT` | No | `8000` | HTTP/SSE bind port |
| `GROK_MCP_PATH` | No | auto | Custom path; `http` defaults to `/mcp/`, `sse` to `/sse/` |
| `GROK_MCP_SHOW_BANNER` | No | `false` | Show FastMCP banner |

### Debug and logs

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROK_DEBUG` | No | `false` | Debug mode |
| `GROK_LOG_LEVEL` | No | `INFO` | Log level |
| `GROK_LOG_DIR` | No | `logs` | Log directory |
| `GROK_RETRY_MAX_ATTEMPTS` | No | `3` | Max retry attempts |
| `GROK_RETRY_MULTIPLIER` | No | `1` | Retry backoff multiplier |
| `GROK_RETRY_MAX_WAIT` | No | `10` | Max retry wait in seconds |

---

## 9. Client setup notes

See the full guide here:

- [`CLIENTS.md`](./CLIENTS.md)

### Cherry Studio

Recommended: `STDIO`

```text
command: uvx
args:
  --from
  git+https://github.com/JARVIS-no1/GrokSearch@main
  grok-search
```

### Chatbox

#### Option A: local stdio (most reliable)

```json
{
  "name": "grok-search",
  "command": "uvx",
  "args": [
    "--from",
    "git+https://github.com/JARVIS-no1/GrokSearch@main",
    "grok-search-stdio"
  ],
  "env": {
    "GROK_API_URL": "https://your-api-endpoint.com/v1",
    "GROK_API_KEY": "your-grok-api-key"
  }
}
```

#### Option B: remote SSE

```text
https://your-domain.example/sse/
```

#### Option C: remote Streamable HTTP

```text
https://your-domain.example/mcp/
```

> If Chatbox reports an `SSE Transport Error`, prefer local stdio first, or switch the remote deployment to `sse`.

### Claude Code / Codex / Cursor

Local stdio is usually the best choice because it is simpler, more stable, and avoids remote auth / proxy / path-rewrite issues.

---

## 10. MCP tools

### `web_search`

AI web search tool.

Returns:

- `session_id`
- `content`
- `sources_count`

### `get_sources`

Retrieves cached sources for a previous `web_search` call.

### `web_fetch`

Fetches page content, Tavily first, then Firecrawl fallback.

### `web_map`

Site structure mapping tool powered by Tavily.

### `get_config_info`

Displays current configuration and tests API connectivity.

### `switch_model`

Changes the default Grok model and persists it locally.

### `toggle_builtin_tools`

Claude Code helper for disabling the built-in WebSearch / WebFetch tools.

### `plan_*`

Structured planning tools for complex retrieval workflows.

---

## 11. Validation

### 1) Verify stdio mode

```bash
grok-search-stdio
```

or:

```bash
claude mcp list
```

### 2) Verify HTTP mode

```bash
GROK_MCP_TRANSPORT=http
GROK_MCP_HOST=127.0.0.1
GROK_MCP_PORT=8000
grok-search
```

Then use:

```text
http://127.0.0.1:8000/mcp/
```

Health check:

```text
http://127.0.0.1:8000/health
```

### 3) Verify SSE mode

```bash
GROK_MCP_TRANSPORT=sse
GROK_MCP_HOST=127.0.0.1
GROK_MCP_PORT=8000
grok-search
```

Then point the client to:

```text
http://127.0.0.1:8000/sse/
```

The health endpoint is still available at:

```text
http://127.0.0.1:8000/health
```

---

## 12. Security notes

If you expose this MCP service publicly, at minimum consider:

- putting it behind a reverse proxy
- adding authentication or access control
- validating `Origin`
- binding to `127.0.0.1` for local-only debugging

---

## 13. FAQ

### Q1: Do I need both Grok and Tavily?

No.

- `GROK_API_URL` + `GROK_API_KEY` are the core requirements
- Tavily / Firecrawl are optional enhancements
- without Tavily, `web_fetch` / `web_map` will be limited

### Q2: Why does Chatbox fail in remote mode?

Common reasons:

- you used `/mcp` instead of `/mcp/`
- the client expects legacy SSE behavior
- your service is running Streamable HTTP, not SSE

Recommended troubleshooting order:

1. try local stdio first
2. then try `/sse/`
3. finally try `/mcp/`

### Q3: What format should the Grok API endpoint use?

It should be OpenAI-compatible and support at least:

- `/chat/completions`
- `/models`

---

## License

[MIT License](../LICENSE)






