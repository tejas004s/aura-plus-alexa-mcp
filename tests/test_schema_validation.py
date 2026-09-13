import pytest
from server.schemas import (
    MCPRequest,
    MCPResponse,
    InitializeResult,
    ToolParamSchema,
    MCPToolDefinition,
    MCPResourceDefinition,
    MCPPromptDefinition,
    ServerCapabilities
)

def test_mcprequest_model():
    req = MCPRequest(method="test", params={"a": 1})
    assert req.jsonrpc == "2.0"
    assert req.method == "test"
    assert req.params == {"a": 1}

def test_mcpresponse_model():
    res = MCPResponse(result={"success": True})
    assert res.jsonrpc == "2.0"
    assert res.result == {"success": True}

def test_initializeresult_defaults():
    ir = InitializeResult()
    assert ir.protocolVersion == "2025-11-25"
    assert ir.capabilities is not None
    assert ir.serverInfo is not None

def test_toolparamschema_serialization():
    tp = ToolParamSchema(properties={"p1": {"type": "string"}})
    d = tp.model_dump()
    assert d["type"] == "object"
    assert "p1" in d["properties"]

def test_mcptooldefinition_serialization():
    tp = ToolParamSchema()
    td = MCPToolDefinition(name="t1", description="desc", inputSchema=tp)
    d = td.model_dump()
    assert d["name"] == "t1"
    assert d["description"] == "desc"

def test_mcpresourcedefinition_fields():
    res = MCPResourceDefinition(uri="app://res", name="Res1")
    assert res.uri == "app://res"
    assert res.name == "Res1"
    assert res.mimeType == "application/json"

def test_mcppromptdefinition_serialization():
    pr = MCPPromptDefinition(name="p1")
    d = pr.model_dump()
    assert d["name"] == "p1"
    assert d["arguments"] is None

def test_servercapabilities():
    sc = ServerCapabilities()
    assert sc.tools == {"listChanged": True}
    assert sc.resources == {"subscribe": True, "listChanged": True}
    assert sc.prompts == {"listChanged": True}
