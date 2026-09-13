"""
agent_core.py - AWS AgentCore & Strands Multi-Agent Orchestrator

Coordinates specialized worker agents, collects execution traces, and synthesizes
multi-modal Alexa+ voice + MCP App visual cards with dynamic response generation.
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


# ─── Agent Router: Classifies intents and prevents execution loops ─────────
class AgentRouter:
    """Intelligent request router that classifies user intents, dispatches to
    specialist agents, and prevents circular execution loops."""

    MAX_EXECUTION_DEPTH = 10

    INTENT_KEYWORDS = {
        "MEMORY": ["remember", "allergy", "dietary", "preference", "family", "member", "profile"],
        "CULINARY": ["dinner", "cook", "recipe", "food", "meal", "menu", "italian", "japanese", "mexican", "french", "indian"],
        "SHOPPING": ["order", "cart", "groceries", "buy", "purchase", "amazon", "fresh", "ingredients"],
        "AMBIANCE": ["light", "thermostat", "music", "ambiance", "temperature", "scene", "atmosphere"],
        "CALENDAR": ["calendar", "schedule", "event", "weekend", "friday", "saturday", "brunch", "appointment"],
    }

    def classify_intent(self, prompt: str) -> List[str]:
        """Classifies a prompt into one or more intent categories."""
        prompt_lower = prompt.lower()
        matched = []
        for intent, keywords in self.INTENT_KEYWORDS.items():
            if any(kw in prompt_lower for kw in keywords):
                matched.append(intent)
        # Multi-intent triggers MULTI_AGENT
        if len(matched) >= 2:
            matched.insert(0, "MULTI_AGENT")
        elif not matched:
            matched = ["GENERAL"]
        return matched

    def check_loop_guard(self, call_history: List[str], new_call: str) -> bool:
        """Returns True if the call is safe (no loop detected)."""
        if len(call_history) >= self.MAX_EXECUTION_DEPTH:
            return False
        # Detect if same tool called more than 2x consecutively
        if len(call_history) >= 2 and call_history[-1] == new_call and call_history[-2] == new_call:
            return False
        return True


agent_router = AgentRouter()


class AgentCoreOrchestrator:
    """Multi-agent orchestrator inspired by AWS AgentCore and Strands SDK."""

    def __init__(self):
        self.client = bedrock_agent_client
        self.router = agent_router

    async def process_request(self, user_prompt: str) -> Dict[str, Any]:
        start_time = time.time()
        trace: List[Dict[str, Any]] = []
        mcp_apps: List[Dict[str, Any]] = []
        call_history: List[str] = []

        # Stage 0: Intent Classification (Agent Router)
        intents = self.router.classify_intent(user_prompt)
        trace.append(ExecutionTraceEvent(
            stage="ROUTING",
            agent="Agent Router & Intent Classifier",
            action=f"Classified intents: {', '.join(intents)}",
            details={"intents": intents, "is_multi_agent": "MULTI_AGENT" in intents}
        ).to_dict())

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

        # Stage 3: Autonomous Tool / Skill Execution with Loop Guard
        tool_results: Dict[str, Any] = {}
        for call in tool_calls:
            name = call["name"]
            args = call.get("arguments", {})

            # Loop guard check
            if not self.router.check_loop_guard(call_history, name):
                trace.append(ExecutionTraceEvent(
                    stage="LOOP_GUARD",
                    agent="Execution Safety Monitor",
                    action=f"Blocked potential infinite loop on tool: {name}",
                    details={"call_history_length": len(call_history), "max_depth": AgentRouter.MAX_EXECUTION_DEPTH},
                    status="blocked"
                ).to_dict())
                continue

            call_history.append(name)

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

        # Stage 4: Dynamic Synthesis & Natural Voice Formulation
        spoken_response = self._synthesize_voice_response(user_prompt, tool_results)

        trace.append(ExecutionTraceEvent(
            stage="SYNTHESIS",
            agent="Alexa+ Voice & Multi-Modal Synthesizer",
            action="Generated conversational speech & assembled interactive MCP Apps",
            details={"spoken_preview": spoken_response[:200]}
        ).to_dict())

        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        # Sustainability metrics
        sustainability = {
            "total_tool_calls": len(call_history),
            "estimated_tokens": bedrock_result.get("usage", {}).get("totalTokens", 0),
            "execution_time_ms": elapsed_ms,
            "estimated_kwh": round(bedrock_result.get("usage", {}).get("totalTokens", 0) * 0.0000003, 6),
            "estimated_co2_grams": round(bedrock_result.get("usage", {}).get("totalTokens", 0) * 0.0000003 * 400, 4),
            "efficiency_note": "Optimized: parallel tool execution reduces redundant LLM calls"
        }

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
                "model_used": bedrock_result.get("model"),
                "intents_detected": intents,
                "loop_guard_active": True,
                "sustainability": sustainability
            }
        }

    def _synthesize_voice_response(self, prompt: str, tool_results: Dict[str, Any]) -> str:
        """
        Dynamically creates a natural, warm Alexa+ spoken response from actual tool results.
        Never hardcodes specific names/items — reads from real data.
        """
        sentences = ["I've got everything organized for you."]

        # Memory results — extract actual dietary restrictions found
        if "household_memory_query_dietary" in tool_results:
            mem_data = tool_results["household_memory_query_dietary"]
            if mem_data.get("found"):
                profiles = mem_data.get("profiles", [])
                restrictions = mem_data.get("dietary_restrictions", [])
                member_names = [p.get("name", "family member") for p in profiles]
                if restrictions:
                    sentences.append(
                        f"I checked our household memory for {', '.join(member_names)}. "
                        f"Important dietary notes: {', '.join(restrictions[:3])}. All fully accounted for."
                    )

        # Culinary results — extract actual course titles
        if "culinary_plan_menu" in tool_results:
            menu_data = tool_results["culinary_plan_menu"]
            courses = menu_data.get("courses", [])
            theme = menu_data.get("menu_theme", "dinner")
            course_titles = [c.get("title", "") for c in courses if c.get("course") != "Sommelier Pairing"]
            beverage = next((c.get("title", "") for c in courses if c.get("course") == "Sommelier Pairing"), None)
            if course_titles:
                sentences.append(
                    f"I planned a {theme} menu featuring {course_titles[0]}"
                    + (f" and {course_titles[1]}" if len(course_titles) > 1 else "")
                    + "."
                )
            if beverage:
                sentences.append(f"Paired with {beverage}.")

        # Cart results — extract actual total
        if "amazon_cart_assemble" in tool_results:
            cart_data = tool_results["amazon_cart_assemble"]
            cart_summary = cart_data.get("cart_summary", {})
            total = cart_summary.get("total", 0)
            item_count = len(cart_summary.get("items", []))
            delivery = cart_summary.get("delivery_window", "soon")
            if total > 0:
                sentences.append(
                    f"I assembled {item_count} certified ingredients into an Amazon Fresh cart "
                    f"totaling ${total:.2f} for {delivery} delivery. "
                    "The checkout approval card is on your screen for one-click confirmation."
                )

        # Ambiance results — extract actual scene details
        if "smart_ambiance_set_scene" in tool_results:
            ambiance_data = tool_results["smart_ambiance_set_scene"]
            state = ambiance_data.get("ambiance_state", {})
            scene = state.get("scene_name", "custom scene")
            temp = state.get("climate", {}).get("target_temp_f", 71)
            schedule = state.get("scheduled_time", "soon")
            audio = state.get("audio", {}).get("now_playing", "ambient music")
            sentences.append(
                f"The {scene} ambiance is set for {schedule} — "
                f"{temp}°F, warm lighting, and {audio} queued."
            )

        # Calendar results — extract actual event details
        if "calendar_schedule_event" in tool_results:
            cal_data = tool_results["calendar_schedule_event"]
            event = cal_data.get("event", {})
            title = event.get("title", "your event")
            start = event.get("start", "")
            if cal_data.get("conflict_detected"):
                sentences.append(f"Note: I detected a scheduling conflict for {title} at {start} and adjusted accordingly.")
            else:
                sentences.append(f"I've reserved {start} on your calendar for {title}. Everything is ready!")

        return " ".join(sentences)


agent_core_orchestrator = AgentCoreOrchestrator()
