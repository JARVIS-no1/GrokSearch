![这是图片](./images/title.png)
<div align="center">

<!-- # Grok Search MCP -->

[English](./docs/README_EN.md) | 简体中文

**Grok-with-Tavily MCP：面向 Claude Code / Cherry Studio / Chatbox / Codex / Cursor 的通用网络搜索 MCP**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0.0+-green.svg)](https://github.com/jlowin/fastmcp)

</div>

---

## 一、项目简介

Grok Search MCP 是一个基于 [FastMCP](https://github.com/jlowin/fastmcp) 构建的 MCP 服务器，采用双引擎架构：

- **Grok**：负责 AI 驱动的网络搜索
- **Tavily**：负责网页抓取与站点映射
- **Firecrawl**：作为 Tavily 失败时的抓取兜底

它为 Claude Code、Cherry Studio、Chatbox、Codex、Cursor 等 MCP 客户端提供统一的实时网络访问能力。

```text
LLM Client ──MCP──► Grok Search Server
                    ├─ web_search  ───► Grok API
                    ├─ web_fetch   ───► Tavily Extract → Firecrawl Scrape
                    └─ web_map     ───► Tavily Map
```

---

## 二、当前版本的通用化改造

本项目现在同时支持三种传输：

- `stdio`：本地客户端首选，兼容性最好
- `http`：Streamable HTTP，适合 Railway / Docker / 云端远程部署
- `sse`：兼容偏旧实现的远程客户端

### 推荐使用原则

1. **本地客户端优先使用 `stdio`**
2. **远程标准部署优先使用 `http` + `/mcp/`**
3. **Chatbox 等兼容性一般的远程客户端，再考虑 `sse` + `/sse/`**

---

## 三、功能特性

- **双引擎搜索**：Grok 搜索 + Tavily 抓取/映射
- **Firecrawl 兜底**：Tavily 失败时自动降级到 Firecrawl
- **OpenAI 兼容接口**：支持任意 Grok 镜像站
- **自动时间注入**：检测“今天 / 最新 / recent”等查询，注入本地时间上下文
- **智能重试**：支持 Retry-After 解析与指数退避
- **多客户端兼容**：适配 Cherry Studio、Chatbox、Claude Code、Codex、Cursor
- **多传输模式**：stdio / Streamable HTTP / SSE
- **Windows 父进程监控**：避免本地 stdio 场景下产生僵尸进程

---

## 四、安装要求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)（推荐）
- 或可用的 `pip`

安装 uv：

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> Windows 用户如遇到环境隔离、证书或依赖问题，建议优先在 WSL 中运行。

---

## 五、默认安装源

当前文档中的安装示例默认使用以下仓库地址：

```text
git+https://github.com/JARVIS-no1/GrokSearch@main
```

如果你后续把代码推送到自己的 GitHub 仓库，再批量替换为你的仓库地址即可。

---

## 六、快速开始

### 1）本地 stdio 方式（推荐）

适用于：

- Claude Code
- Cherry Studio
- Codex / Cursor
- Chatbox 的本地 MCP

#### 使用 uvx 直接运行

```bash
uvx --from git+https://github.com/JARVIS-no1/GrokSearch@main grok-search
```

或显式指定 stdio：

```bash
uvx --from git+https://github.com/JARVIS-no1/GrokSearch@main grok-search-stdio
```

### 2）本地安装后运行

```bash
pip install .
```

默认入口：

```bash
grok-search
```

显式入口：

```bash
grok-search-stdio
grok-search-http
grok-search-sse
```

---

## 七、远程部署

### Docker / Railway 默认模式

项目当前 Dockerfile 默认使用：

- `GROK_MCP_TRANSPORT=http`
- 监听 `0.0.0.0:${PORT}`
- 默认路径 `/mcp/`
- 健康检查路径 `/health`

默认远程 MCP 地址：

```text
https://your-domain.example/mcp/
```

健康检查地址：

```text
https://your-domain.example/health
```

### 如果要兼容 Chatbox 远程模式

部署时把环境变量改成：

```bash
GROK_MCP_TRANSPORT=sse
```

此时默认路径切换为：

```text
https://your-domain.example/sse/
```

### Railway 模板

仓库里已新增：

- `railway.json.example`
- `docs/RAILWAY.md`

如果你准备直接部署到 Railway，先看：

- [`docs/RAILWAY.md`](./docs/RAILWAY.md)

---

## 八、环境变量

### 核心 API 配置

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `GROK_API_URL` | ✅ | - | Grok API 地址，需兼容 OpenAI 格式 |
| `GROK_API_KEY` | ✅ | - | Grok API 密钥 |
| `GROK_MODEL` | ❌ | `grok-4-fast` | 默认模型 |
| `TAVILY_API_KEY` | ❌ | - | Tavily API 密钥 |
| `TAVILY_API_URL` | ❌ | `https://api.tavily.com` | Tavily API 地址 |
| `TAVILY_ENABLED` | ❌ | `true` | 是否启用 Tavily |
| `FIRECRAWL_API_KEY` | ❌ | - | Firecrawl API 密钥 |
| `FIRECRAWL_API_URL` | ❌ | `https://api.firecrawl.dev/v2` | Firecrawl API 地址 |

### MCP 传输配置

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `GROK_MCP_TRANSPORT` | ❌ | `stdio` | `stdio` / `http` / `sse` |
| `GROK_MCP_HOST` | ❌ | `127.0.0.1` | HTTP/SSE 监听地址 |
| `GROK_MCP_PORT` | ❌ | `8000` | HTTP/SSE 监听端口 |
| `GROK_MCP_PATH` | ❌ | 自动 | 自定义 MCP 路径；`http` 默认 `/mcp/`，`sse` 默认 `/sse/` |
| `GROK_MCP_SHOW_BANNER` | ❌ | `false` | 是否显示 FastMCP banner |

### 调试与日志

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `GROK_DEBUG` | ❌ | `false` | 调试模式 |
| `GROK_LOG_LEVEL` | ❌ | `INFO` | 日志级别 |
| `GROK_LOG_DIR` | ❌ | `logs` | 日志目录 |
| `GROK_RETRY_MAX_ATTEMPTS` | ❌ | `3` | 最大重试次数 |
| `GROK_RETRY_MULTIPLIER` | ❌ | `1` | 重试退避乘数 |
| `GROK_RETRY_MAX_WAIT` | ❌ | `10` | 最大等待秒数 |

---

## 九、客户端配置建议

更完整说明见：

- [`docs/CLIENTS.md`](./docs/CLIENTS.md)

### 1）Cherry Studio

推荐 `STDIO`：

- 命令：`uvx`
- 参数：

```text
--from
git+https://github.com/JARVIS-no1/GrokSearch@main
grok-search
```

### 2）Chatbox

#### 方案 A：本地 stdio（最稳）

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

#### 方案 B：远程 SSE

```text
https://your-domain.example/sse/
```

#### 方案 C：远程 Streamable HTTP

```text
https://your-domain.example/mcp/
```

> 如果 Chatbox 远程模式报 `SSE Transport Error`，优先回退到本地 stdio，或将远程部署改为 `sse`。

### 3）Claude Code / Codex / Cursor

推荐直接使用本地 stdio，因为：

- 配置简单
- 权限边界更清晰
- 生命周期更稳定
- 避免远程鉴权与代理问题

---

## 十、MCP 工具

### `web_search`

AI 网络搜索工具。

返回：

- `session_id`
- `content`
- `sources_count`

### `get_sources`

根据 `session_id` 获取 `web_search` 的信源列表。

### `web_fetch`

抓取网页正文，优先 Tavily，失败时自动降级到 Firecrawl。

### `web_map`

站点结构映射工具，依赖 Tavily。

### `get_config_info`

显示配置状态，并测试 Grok API 连通性。

### `switch_model`

切换默认 Grok 模型，配置持久化到本地配置文件。

### `toggle_builtin_tools`

用于 Claude Code 项目内一键禁用官方 WebSearch / WebFetch。

### `plan_*`

结构化搜索规划工具集，适合复杂检索流程。

---

## 十一、验证方式

### 1）验证是否安装成功

```bash
grok-search-stdio
```

或：

```bash
claude mcp list
```

### 2）验证 HTTP 模式

```bash
GROK_MCP_TRANSPORT=http
GROK_MCP_HOST=127.0.0.1
GROK_MCP_PORT=8000
grok-search
```

然后访问：

```text
http://127.0.0.1:8000/mcp/
```

健康检查：

```text
http://127.0.0.1:8000/health
```

### 3）验证 SSE 模式

```bash
GROK_MCP_TRANSPORT=sse
GROK_MCP_HOST=127.0.0.1
GROK_MCP_PORT=8000
grok-search
```

然后客户端填：

```text
http://127.0.0.1:8000/sse/
```

健康检查仍然可用：

```text
http://127.0.0.1:8000/health
```

---

## 十二、安全建议

如果你将 MCP 暴露到公网，建议至少做到：

- 通过反向代理接入
- 增加认证或访问控制
- 校验 `Origin`
- 内网调试时尽量绑定 `127.0.0.1`

---

## 十三、常见问题

### Q1：必须同时配置 Grok 和 Tavily 吗？

不是。

- `GROK_API_URL` + `GROK_API_KEY` 是核心必填
- Tavily / Firecrawl 都是可选增强
- 不配 Tavily 时，`web_fetch` / `web_map` 能力会受限

### Q2：为什么远程模式在 Chatbox 报错？

常见原因：

- 你填的是 `/mcp` 不是 `/mcp/`
- 客户端更偏向 legacy SSE
- 你的服务当前跑的是 Streamable HTTP，而非 SSE

优先解决顺序：

1. 先试本地 stdio
2. 再试 `/sse/`
3. 最后再尝试 `/mcp/`

### Q3：Grok API 地址要求什么格式？

需要兼容 OpenAI 格式，至少支持：

- `/chat/completions`
- `/models`

---

## 许可证

[MIT License](LICENSE)

---

<div align="center">

**如果这个项目对您有帮助，欢迎点个 Star。**

</div>








