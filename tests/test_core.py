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


# ---------- 未经标准入口启动时，写入工具默认禁用 ----------
def test_admin_tools_disabled_for_unknown_entry(monkeypatch):
    monkeypatch.delenv("GROK_ENABLE_ADMIN_TOOLS", raising=False)
    monkeypatch.setattr(server, "_ACTIVE_TRANSPORT", None)
    assert server._admin_tools_allowed() is False


def test_get_http_app_requires_token(monkeypatch):
    monkeypatch.delenv("GROK_MCP_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("GROK_MCP_ALLOW_NO_AUTH", raising=False)
    with pytest.raises(RuntimeError):
        server.get_http_app()


# ---------- 单会话资源上限 ----------
def test_planning_rejects_oversized_input():
    from grok_search import planning
    eng = PlanningEngine()
    sid = eng.process_phase("intent_analysis", "t")["session_id"]
    big = {"x": "a" * (planning._MAX_PHASE_DATA_CHARS + 10)}
    assert "error" in eng.process_phase("query_decomposition", "t", session_id=sid, phase_data=big)
    for _ in range(planning._MAX_LIST_ITEMS):
        eng.process_phase("query_decomposition", "t", session_id=sid, phase_data={"q": 1})
    r = eng.process_phase("query_decomposition", "t", session_id=sid, phase_data={"q": 1})
    assert "error" in r
    long = eng.process_phase("intent_analysis", "x" * 10000, session_id=sid, is_revision=True)
    assert "error" not in long
    assert len(eng.get_session(sid).phases["intent_analysis"].thought) == planning._MAX_THOUGHT_CHARS


# ---------- 启动异常时退出码非 0 ----------
def test_crash_exits_nonzero():
    env = {
        **os.environ,
        "GROK_API_URL": "http://127.0.0.1:9",
        "GROK_API_KEY": "x",
        "GROK_MCP_TRANSPORT": "http",
        "GROK_MCP_HOST": "127.0.0.1",
        "GROK_MCP_PORT": "not-a-port",
    }
    r = subprocess.run([sys.executable, "-m", "grok_search.server"], env=env,
                       capture_output=True, text=True, timeout=30)
    assert r.returncode != 0


# ---------- 端到端：真实 HTTP 服务的鉴权链路与写入工具拒绝 ----------
def _free_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_end_to_end_auth_and_admin_block():
    import httpx
    port = _free_port()
    env = {
        **os.environ,
        "GROK_API_URL": "http://127.0.0.1:9",
        "GROK_API_KEY": "x",
        "GROK_MCP_TRANSPORT": "http",
        "GROK_MCP_HOST": "127.0.0.1",
        "GROK_MCP_PORT": str(port),
        "GROK_MCP_AUTH_TOKEN": "e2e-token",
    }
    env.pop("GROK_ENABLE_ADMIN_TOOLS", None)
    proc = subprocess.Popen([sys.executable, "-m", "grok_search.server"], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    client = httpx.Client(trust_env=False, timeout=5)  # 不走系统代理
    try:
        for _ in range(60):
            try:
                if client.get(f"{base}/health").status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.25)
        else:
            pytest.fail("server did not start")

        hdr = {"content-type": "application/json", "accept": "application/json, text/event-stream"}
        init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                           "clientInfo": {"name": "t", "version": "1"}}}
        assert client.post(f"{base}/mcp/", json=init, headers=hdr).status_code == 401

        auth = {**hdr, "authorization": "Bearer e2e-token"}
        r = client.post(f"{base}/mcp/", json=init, headers=auth)
        assert r.status_code == 200
        sid = r.headers["mcp-session-id"]
        auth["mcp-session-id"] = sid
        client.post(f"{base}/mcp/", headers=auth,
                   json={"jsonrpc": "2.0", "method": "notifications/initialized"})
        r = client.post(f"{base}/mcp/", headers=auth, json={
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "switch_model", "arguments": {"model": "x"}}})
        assert "已禁用" in r.text
    finally:
        client.close()
        proc.terminate()
        proc.wait(timeout=10)
