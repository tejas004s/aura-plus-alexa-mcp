"""
test_mcp_spec.py - Verification tests for MCP Specification 2025-11-25+
"""

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from server.mcp_server import router

app = FastAPI()
app.include_router(router)


@pytest.mark.asyncio
async def test_mcp_initialize():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        res = await ac.post("/mcp/message", json=req)
        assert res.status_code == 200
        data = res.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "protocolVersion" in data["result"]
        assert data["result"]["protocolVersion"] == "2025-11-25"
        assert "capabilities" in data["result"]
        assert "serverInfo" in data["result"]


@pytest.mark.asyncio
async def test_mcp_tools_list():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        res = await ac.post("/mcp/message", json=req)
        assert res.status_code == 200
        data = res.json()
        assert "tools" in data["result"]
        tool_names = [t["name"] for t in data["result"]["tools"]]
        assert "household_memory_get_summary" in tool_names
        assert "amazon_cart_assemble" in tool_names
        assert "smart_ambiance_set_scene" in tool_names
        assert "culinary_plan_menu" in tool_names


@pytest.mark.asyncio
async def test_mcp_tools_call():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "household_memory_query_dietary",
                "arguments": {"member_name": "Mom"}
            }
        }
        res = await ac.post("/mcp/message", json=req)
        assert res.status_code == 200
        data = res.json()
        assert "content" in data["result"]
        assert len(data["result"]["content"]) > 0
        assert data["result"]["content"][0]["type"] == "text"


@pytest.mark.asyncio
async def test_mcp_resources_list_and_read():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        req_list = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/list",
            "params": {}
        }
        res = await ac.post("/mcp/message", json=req_list)
        assert res.status_code == 200
        assert "resources" in res.json()["result"]

        req_read = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/read",
            "params": {"uri": "household://profile"}
        }
        res_read = await ac.post("/mcp/message", json=req_read)
        assert res_read.status_code == 200
        assert "contents" in res_read.json()["result"]
