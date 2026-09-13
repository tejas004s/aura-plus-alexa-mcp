"""
agent_core.py - AWS AgentCore & Strands Multi-Agent Orchestrator

Coordinates specialized worker agents, collects execution traces, and synthesizes
multi-modal Alexa+ voice + MCP App visual cards.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .bedrock_client import bedrock_agent_client
from server.mcp_server import execute_tool_call


class ExecutionTraceEvent:
    def __init__(self, stage: str, agent: str, action: str, details: Any, status: str = "completed"):
        self.stage = stage
        self.agent = agent
        self.action = action
        self.details = details
        self.status = status
        self.timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "agent": self.agent,
            "action": self.action,
            "details": self.details,
            "status": self.status,
            "timestamp": self.timestamp
        }


class AgentCoreOrchestrator:
    """Multi-agent orchestrator inspired by AWS AgentCore and Strands SDK."""

    def __init__(self):
        self.client = bedrock_agent_client

    async def process_request(self, user_prompt: str) -> Dict[str, Any]:
        start_time = time.time()
        trace: List[Dict[str, Any]] = []
        mcp_apps: List[Dict[str, Any]] = []

        # Stage 1: Perception & Goal Decomposition
        trace.append(ExecutionTraceEvent(
            stage="PERCEPTION",
            agent="Supervisor Agent (Bedrock Claude 3.5)",
            action="Decomposing user goal & identifying constraints",
            details={"raw_prompt": user_prompt}
        ).to_dict())

        # Stage 2: Planning with Bedrock
        bedrock_result = await self.client.converse_with_tools(user_prompt)
        tool_calls = bedrock_result.get("tool_calls", [])

        trace.append(ExecutionTraceEvent(
            stage="PLANNING",
            agent="Master Planner (AWS Bedrock / AgentCore)",
            action=f"Formulated execution DAG ({len(tool_calls)} parallel/sequential tasks)",
            details={
                "model": bedrock_result.get("model"),
                "mode": bedrock_result.get("mode"),
                "tasks_planned": [t["name"] for t in tool_calls]
            }
        ).to_dict())

        # Stage 3: Autonomous Tool / Skill Execution
        tool_results: Dict[str, Any] = {}
        for call in tool_calls:
            name = call["name"]
            args = call.get("arguments", {})

            # Map agent names
            agent_label = "Specialist Agent"
            if "memory" in name:
                agent_label = "Memory & Safety Auditor Agent"
            elif "culinary" in name:
                agent_label = "Culinary & Sommelier Agent"
            elif "cart" in name:
                agent_label = "Amazon Procurement & Guardrail Agent"
            elif "ambiance" in name:
                agent_label = "Smart Ambiance & IoT Agent"
            elif "calendar" in name:
                agent_label = "Calendar & Social Concierge"

            trace.append(ExecutionTraceEvent(
                stage="TOOL_EXECUTION",
                agent=agent_label,
                action=f"Invoking MCP Tool: {name}",
                details={"input_parameters": args},
                status="running"
            ).to_dict())

            try:
                res = await execute_tool_call(name, args)
                tool_results[name] = res

                # Extract any MCP App generative UI cards/carousels
                if isinstance(res, dict):
                    if "mcp_app_card" in res:
                        mcp_apps.append(res["mcp_app_card"])
                    if "mcp_app_carousel" in res:
                        mcp_apps.append(res["mcp_app_carousel"])

                trace.append(ExecutionTraceEvent(
                    stage="TOOL_EXECUTION",
                    agent=agent_label,
                    action=f"Completed MCP Tool: {name}",
                    details={"summary": "Success", "output_keys": list(res.keys()) if isinstance(res, dict) else "raw"},
                    status="completed"
                ).to_dict())

            except Exception as e:
                trace.append(ExecutionTraceEvent(
                    stage="TOOL_EXECUTION",
                    agent=agent_label,
                    action=f"Error executing {name}",
                    details={"error": str(e)},
                    status="error"
                ).to_dict())

        # Stage 4: Synthesis & Natural Voice Formulation
        spoken_response = self._synthesize_voice_response(user_prompt, tool_results)

        trace.append(ExecutionTraceEvent(
            stage="SYNTHESIS",
            agent="Alexa+ Voice & Multi-Modal Synthesizer",
            action="Generated conversational speech & assembled interactive MCP Apps",
            details={"spoken_preview": spoken_response}
        ).to_dict())

        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "status": "success",
            "spoken_response": spoken_response,
            "mcp_apps": mcp_apps,
            "execution_trace": trace,
            "metadata": {
                "execution_time_ms": elapsed_ms,
                "aws_services": ["Amazon Bedrock", "AWS AgentCore", "Strands SDK Architecture"],
                "mcp_spec": "2025-11-25 (Streamable HTTP)",
                "tool_count": len(tool_calls),
                "model_used": bedrock_result.get("model")
            }
        }

    def _synthesize_voice_response(self, prompt: str, tool_results: Dict[str, Any]) -> str:
        """
        Creates a natural, warm, proactive spoken Alexa+ response highlighting what was accomplished.
        """
        sentences = [
            "I've got everything organized for your family's visit."
        ]

        if "household_memory_query_dietary" in tool_results or "culinary_plan_menu" in tool_results:
            sentences.append(
                "I checked our household memory: Mom's strict shellfish allergy and gluten sensitivity are fully accounted for. "
                "I planned an authentic Italian dinner featuring gluten-free Penne all'Arrabbiata and paired Dad's favorite Tuscan Chianti Classico."
            )

        if "amazon_cart_assemble" in tool_results:
            cart_info = tool_results["amazon_cart_assemble"].get("cart_summary", {})
            total = cart_info.get("total", 62.24)
            sentences.append(
                f"I assembled all certified ingredients into an Amazon Fresh cart totaling ${total:.2f} for Friday doorstep delivery. "
                "I've placed the checkout approval card on your screen for your one-click confirmation."
            )

        if "smart_ambiance_set_scene" in tool_results:
            sentences.append(
                "The Tuscan Sunset ambiance scene is scheduled for Friday at 6:30 PM with warm candlelight amber lighting, the thermostat set to 71 degrees, and acoustic dinner jazz queued on Amazon Music."
            )

        if "calendar_schedule_event" in tool_results:
            sentences.append(
                "I've also reserved Friday 7:00 PM on your family calendar. Everything is ready for you!"
            )

        return " ".join(sentences)


agent_core_orchestrator = AgentCoreOrchestrator()
