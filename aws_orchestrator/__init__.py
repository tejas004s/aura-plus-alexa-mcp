"""
aws_orchestrator package
"""

from .bedrock_client import bedrock_agent_client, BedrockAgentClient
from .agent_core import agent_core_orchestrator, AgentCoreOrchestrator
from .prompts import MASTER_PLANNER_SYSTEM_PROMPT, BEDROCK_TOOL_SPECS

__all__ = [
    "bedrock_agent_client",
    "BedrockAgentClient",
    "agent_core_orchestrator",
    "AgentCoreOrchestrator",
    "MASTER_PLANNER_SYSTEM_PROMPT",
    "BEDROCK_TOOL_SPECS"
]
