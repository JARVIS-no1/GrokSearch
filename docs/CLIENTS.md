# Grok Search MCP 客户端接入建议

这个项目现在同时支持：

- `stdio`：本地客户端首选，兼容面最广
- `http`：Streamable HTTP，适合远程部署
- `sse`：兼容旧式远程客户端

## 推荐原则

优先级建议：

1. **本地客户端优先用 `stdio`**
2. **远程标准优先用 `http` / `/mcp/`**
3. **旧客户端或只支持 http+sse 的客户端，再用 `sse` / `/sse/`**

原因：

- MCP 官方当前标准传输是 `stdio` 和 **Streamable HTTP**
- 旧版 `HTTP+SSE` 主要用于兼容历史客户端
- 一些桌面客户端虽然支持远程 MCP，但实现仍偏向 legacy SSE

## 默认安装源

本文中的安装示例默认使用以下仓库地址：

```text
git+https://github.com/JARVIS-no1/GrokSearch@main
```

## 环境变量

```bash
GROK_MCP_TRANSPORT=stdio|http|sse
GROK_MCP_HOST=127.0.0.1
GROK_MCP_PORT=8000
GROK_MCP_PATH=/mcp/
GROK_MCP_SHOW_BANNER=false
```

说明：

- `stdio` 模式下忽略 `HOST/PORT/PATH`
- `http` 默认路径为 `/mcp/`
- `sse` 默认路径为 `/sse/`
- 若显式设置 `GROK_MCP_PATH`，会覆盖默认路径

## Cherry Studio

Cherry Studio 官方文档当前主流配置仍然是 `STDIO`。

推荐配置：

- 类型：`STDIO`
- 命令：`uvx`
- 参数：

```text
--from
git+https://github.com/JARVIS-no1/GrokSearch@main
grok-search
```

如需显式指定 stdio：

```text
--from
git+https://github.com/JARVIS-no1/GrokSearch@main
grok-search-stdio
```

## Chatbox

Chatbox 同时支持：

- 本地 `command/args/env`
- 远程 `url`

### 方案 A：本地 stdio（最稳）

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

### 方案 B：远程 SSE（兼容旧客户端）

先用：

```bash
GROK_MCP_TRANSPORT=sse
```

部署后把 Chatbox URL 指向：

```text
https://your-domain.example/sse/
```

### 方案 C：远程 Streamable HTTP

先用：

```bash
GROK_MCP_TRANSPORT=http
```

部署后 URL：

```text
https://your-domain.example/mcp/
```

如果客户端对 Streamable HTTP 兼容不好，优先回退到 `stdio` 或 `sse`。

## Claude Code / Codex / Cursor

这类客户端通常更适合 `stdio`，因为：

- 配置最直接
- 本地权限与生命周期更清晰
- 避免远程鉴权、反向代理、路径重写问题

如果必须远程部署，优先使用：

```bash
GROK_MCP_TRANSPORT=http
```

## Railway / Docker

镜像默认环境：

```bash
GROK_MCP_TRANSPORT=http
GROK_MCP_HOST=0.0.0.0
```

因此默认暴露：

```text
/mcp/
```

若要兼容 Chatbox 这类偏 SSE 的客户端，只需要把部署环境变量改成：

```bash
GROK_MCP_TRANSPORT=sse
```

默认路径会自动切换为：

```text
/sse/
```

## 安全提示

MCP 官方对 Streamable HTTP 的建议包括：

- 校验 `Origin`
- 本地运行时优先绑定 `127.0.0.1`
- 对公网服务增加鉴权

因此公网部署时建议至少放在反向代理之后，并补充认证策略。



