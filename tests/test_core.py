import asyncio
import os
import subprocess
import sys
import time

import pytest

from grok_search.config import config
from grok_search.planning import PlanningEngine
from grok_search.sources import SourcesCache, new_session_id
from grok_search import server


# ---------- 密钥不回显 ----------
def test_mask_never_reveals_fragments():
    assert config._mask_api_key("sk-1234567890abcdef") == "已配置"
    assert config._mask_api_key(None) == "未配置"


# ---------- session id 足够长 ----------
def test_session_id_is_128_bit():
    assert len(new_session_id()) == 32


# ---------- 规划会话：容量与过期 ----------
def test_planning_capacity_limit():
    eng = PlanningEngine(max_sessions=3, ttl_seconds=3600)
    ids = [eng.process_phase("intent_analysis", "t")["session_id"] for _ in range(5)]
    assert len(eng._sessions) == 3
    assert eng.get_session(ids[0]) is None
    assert eng.get_session(ids[-1]) is not None


def test_planning_ttl_expiry():
    eng = PlanningEngine(max_sessions=10, ttl_seconds=0.05)
    sid = eng.process_phase("intent_analysis", "t")["session_id"]
    time.sleep(0.1)
    assert eng.get_session(sid) is None


# ---------- 信源缓存：容量与过期 ----------
async def test_sources_cache_ttl_and_size():
    cache = SourcesCache(max_size=2, ttl_seconds=0.05)
    await cache.set("a", [{"url": "1"}])
    await cache.set("b", [{"url": "2"}])
    await cache.set("c", [{"url": "3"}])
    assert await cache.get("a") is None
    assert await cache.get("c") == [{"url": "3"}]
    await asyncio.sleep(0.1)
    assert await cache.get("c") is None


# ---------- 鉴权中间件 ----------
async def _call(mw, path, headers):
    sent = []

    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    async def send(msg):
        sent.append(msg)

    async def receive():
        return {"type": "http.request", "body": b""}

    m = server._BearerAuthMiddleware(app, token=mw)
    await m({"type": "http", "path": path, "headers": headers}, receive, send)
    return sent[0]["status"]


async def test_auth_middleware():
    assert await _call("s3cret", "/mcp/", []) == 401
    assert await _call("s3cret", "/mcp/", [(b"authorization", b"Bearer wrong")]) == 401
    assert await _call("s3cret", "/mcp/", [(b"authorization", b"Bearer s3cret")]) == 200
    assert await _call("s3cret", "/health", []) == 200


# ---------- 写入类工具在远程模式下默认禁用 ----------
def test_admin_tools_gating(monkeypatch):
    monkeypatch.delenv("GROK_ENABLE_ADMIN_TOOLS", raising=False)
    monkeypatch.setattr(server, "_ACTIVE_TRANSPORT", "stdio")
    assert server._admin_tools_allowed() is True
    monkeypatch.setattr(server, "_ACTIVE_TRANSPORT", "http")
    assert server._admin_tools_allowed() is False
    monkeypatch.setenv("GROK_ENABLE_ADMIN_TOOLS", "true")
    assert server._admin_tools_allowed() is True


# ---------- 非本机监听且无 token 时拒绝启动 ----------
def test_refuses_public_bind_without_token():
    env = {
        **os.environ,
        "GROK_API_URL": "http://127.0.0.1:9",
        "GROK_API_KEY": "x",
        "GROK_MCP_TRANSPORT": "http",
        "GROK_MCP_HOST": "0.0.0.0",
        "GROK_MCP_PORT": "18777",
    }
    env.pop("GROK_MCP_AUTH_TOKEN", None)
    env.pop("GROK_MCP_ALLOW_NO_AUTH", None)
    r = subprocess.run(
        [sys.executable, "-m", "grok_search.server"],
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 2
    assert "GROK_MCP_AUTH_TOKEN" in r.stderr
