"""
schemas.py - Model Context Protocol (MCP) JSON-RPC 2.0 Data Models

Conforming to MCP Specification (Version 2025-11-25+).
"""

from typing import Dict, Any, List, Optional, Union, Literal
from pydantic import BaseModel, Field


class MCPRequest(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class ServerCapabilities(BaseModel):
    tools: Dict[str, bool] = Field(default_factory=lambda: {"listChanged": True})
    resources: Dict[str, bool] = Field(default_factory=lambda: {"subscribe": True, "listChanged": True})
    prompts: Dict[str, bool] = Field(default_factory=lambda: {"listChanged": True})
    logging: Dict[str, bool] = Field(default_factory=dict)


class ServerInfo(BaseModel):
    name: str = "AlexaPlus-Aura-MCP"
    version: str = "1.0.0"
    specVersion: str = "2025-11-25"


class InitializeResult(BaseModel):
    protocolVersion: str = "2025-11-25"
    capabilities: ServerCapabilities = Field(default_factory=ServerCapabilities)
    serverInfo: ServerInfo = Field(default_factory=ServerInfo)
    instructions: str = (
        "Aura+ Autonomous Household & Executive Concierge MCP Server for Alexa+. "
        "Provides Agent Skills for cross-session household memory, culinary planning, "
        "Amazon Fresh purchasing with human-in-the-loop approval, ambiance orchestration, and calendar management."
    )


class ToolParamSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: Optional[List[str]] = Field(default_factory=list)


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    inputSchema: ToolParamSchema


class MCPResourceDefinition(BaseModel):
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = "application/json"


class MCPPromptDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None
