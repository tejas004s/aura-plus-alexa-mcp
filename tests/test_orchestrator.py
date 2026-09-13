"""
test_orchestrator.py - End-to-end multi-agent workflow tests
"""

import pytest
from aws_orchestrator.agent_core import agent_core_orchestrator


@pytest.mark.asyncio
async def test_full_autonomous_orchestration():
    user_prompt = "My parents are visiting this Friday evening for dinner. Prepare the house, plan an Italian dinner, order groceries, and set the ambiance."
    result = await agent_core_orchestrator.process_request(user_prompt)

    assert result["status"] == "success"
    assert "spoken_response" in result
    assert len(result["spoken_response"]) > 0

    # Verify execution trace
    assert "execution_trace" in result
    stages = [step["stage"] for step in result["execution_trace"]]
    assert "PERCEPTION" in stages
    assert "PLANNING" in stages
    assert "TOOL_EXECUTION" in stages
    assert "SYNTHESIS" in stages

    # Verify MCP App Generative UI items
    assert "mcp_apps" in result
    assert len(result["mcp_apps"]) >= 3

    # Verify AWS metadata
    assert "Amazon Bedrock" in result["metadata"]["aws_services"]
