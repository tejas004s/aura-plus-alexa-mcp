import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from server.schemas import MCPRequest, InitializeResult

@pytest.mark.asyncio
async def test_jsonrpc_compliance_and_id_echo():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        req = {"jsonrpc": "2.0", "id": 123, "method": "initialize", "params": {}}
        response = await client.post("/mcp/message", json=req)
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 123

@pytest.mark.asyncio
async def test_invalid_method_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        req = {"jsonrpc": "2.0", "id": 1, "method": "unknown/method", "params": {}}
        response = await client.post("/mcp/message", json=req)
        data = response.json()
        assert data["error"]["code"] == -32601

@pytest.mark.asyncio
async def test_missing_required_arguments_mcp_request():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        req = {"id": 1, "params": {}}  # missing method and jsonrpc (which defaults)
        response = await client.post("/mcp/message", json=req)
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_tools_call_unknown_tool():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "fake_tool"}}
        response = await client.post("/mcp/message", json=req)
        data = response.json()
        assert data["error"]["code"] == -32601

@pytest.mark.asyncio
async def test_resources_read_unknown_uri():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        req = {"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": "fake://uri"}}
        response = await client.post("/mcp/message", json=req)
        data = response.json()
        assert data["error"]["code"] == -32000

@pytest.mark.asyncio
async def test_initialize_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        req = {"jsonrpc": "2.0", "id": 4, "method": "initialize", "params": {}}
        response = await client.post("/mcp/message", json=req)
        data = response.json()
        res = data["result"]
        assert "protocolVersion" in res
        assert "capabilities" in res
        assert "serverInfo" in res
        assert "instructions" in res

@pytest.mark.asyncio
async def test_capabilities_include_tools_resources_prompts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        req = {"jsonrpc": "2.0", "id": 5, "method": "initialize", "params": {}}
        response = await client.post("/mcp/message", json=req)
        data = response.json()
        cap = data["result"]["capabilities"]
        assert "tools" in cap
        assert "resources" in cap
        assert "prompts" in cap

@pytest.mark.asyncio
async def test_tools_list_schema():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        req = {"jsonrpc": "2.0", "id": 6, "method": "tools/list", "params": {}}
        response = await client.post("/mcp/message", json=req)
        data = response.json()
        tools = data["result"]["tools"]
        assert len(tools) > 0
        for tool in tools:
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"

@pytest.mark.asyncio
async def test_prompts_list_valid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        req = {"jsonrpc": "2.0", "id": 7, "method": "prompts/list", "params": {}}
        response = await client.post("/mcp/message", json=req)
        data = response.json()
        prompts = data["result"]["prompts"]
        assert len(prompts) > 0
        for p in prompts:
            assert "name" in p

@pytest.mark.asyncio
async def test_each_tool_has_description():
    from server.mcp_server import TOOLS_REGISTRY
    for tool_name, tool_def in TOOLS_REGISTRY.items():
        assert tool_def.description is not None
        assert len(tool_def.description) > 0

@pytest.mark.asyncio
async def test_each_resource_has_uri_and_name():
    from server.mcp_server import RESOURCES_REGISTRY
    for uri, res_def in RESOURCES_REGISTRY.items():
        assert res_def.uri == uri
        assert res_def.name is not None
