# Railway 部署说明

本项目已经提供 Dockerfile，Railway 检测到 Dockerfile 后会自动使用 Dockerfile 构建。

## 1. 推荐部署方式

推荐直接从 GitHub 仓库部署：

1. 将项目推送到你自己的仓库
2. 在 Railway 中选择 **Deploy from GitHub repo**
3. 选择你的仓库
4. 设置环境变量
5. 部署

## 2. 建议的仓库结构

项目根目录包含：

- `Dockerfile`
- `pyproject.toml`
- `src/`
- `railway.json.example`

如果你准备启用 Railway 配置文件，可以把：

```text
railway.json.example
```

复制并重命名为：

```text
railway.json
```

## 3. 建议设置的环境变量

最少需要：

```bash
GROK_API_URL=https://your-api-endpoint.com/v1
GROK_API_KEY=your-grok-api-key
```

如果你还要启用抓取能力：

```bash
TAVILY_API_KEY=tvly-your-tavily-key
TAVILY_API_URL=https://api.tavily.com
FIRECRAWL_API_KEY=your-firecrawl-key
FIRECRAWL_API_URL=https://api.firecrawl.dev/v2
```

## 4. 选择远程传输模式

### 标准远程模式（推荐）

```bash
GROK_MCP_TRANSPORT=http
```

部署后访问：

```text
https://your-domain.example/mcp/
```

### Chatbox 兼容模式

```bash
GROK_MCP_TRANSPORT=sse
```

部署后访问：

```text
https://your-domain.example/sse/
```

## 5. Health Check

这个项目暴露的是 MCP 端点，不是普通网站首页。

对于某些 MCP 传输：

- `/mcp/` 可能不是一个返回 `200 OK` 的普通浏览器页面
- `/sse/` 也不是传统健康检查页面

现在项目已经提供 `/health` 路由，因此 Railway 可以安全配置健康检查。

推荐将健康检查路径配置为 `/health`。

## 6. Railway Config as Code

根据 Railway 官方文档：

- Railway 支持 `railway.toml` 或 `railway.json`
- 配置文件会覆盖当次部署的 build/deploy 设置
- Dockerfile 存在时，Railway 会优先按 Dockerfile 构建

因此本项目模板只保留最小必要配置。

## 7. 一个典型流程

1. fork 仓库到你自己的 GitHub
2. 把示例中的仓库地址替换成你的 fork
3. 在 Railway 导入仓库
4. 设置 `GROK_API_URL` / `GROK_API_KEY`
5. 选择 `GROK_MCP_TRANSPORT=http` 或 `sse`
6. 部署
7. 在客户端填：
   - `https://your-domain.example/mcp/`
   - 或 `https://your-domain.example/sse/`

## 8. 常见坑

### 1）路径少了最后的 `/`

尽量使用：

```text
/mcp/
/sse/
```

不要偷懒写成：

```text
/mcp
/sse
```

### 2）Chatbox 连 `/mcp/` 报 SSE 错误

优先切到：

```bash
GROK_MCP_TRANSPORT=sse
```

### 3）公网暴露后被任意访问

至少建议：

- 放在反向代理后面
- 加认证
- 控制来源



