"""
bedrock_client.py - Amazon Bedrock Runtime Client & Agent Invocation Layer

Integrates boto3 Bedrock Runtime with Converse API tool calling and automatic
high-fidelity fallback when credentials are not yet configured.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from .prompts import MASTER_PLANNER_SYSTEM_PROMPT, BEDROCK_TOOL_SPECS

logger = logging.getLogger("BedrockClient")


class BedrockAgentClient:
    """Client for Amazon Bedrock with Anthropic Claude 3.5/3.7 and Amazon Nova."""

    def __init__(
        self,
        region_name: str = "us-east-1",
        model_id: str = "amazon.nova-pro-v1:0"
    ):
        self.region_name = os.environ.get("AWS_REGION", region_name)
        self.model_id = os.environ.get("BEDROCK_MODEL_ID", model_id)
        self._client = None
        self._has_credentials = False
        self._init_client()

    def _init_client(self) -> None:
        try:
            session = boto3.Session(region_name=self.region_name)
            creds = session.get_credentials()
            if creds and creds.access_key:
                self._client = session.client("bedrock-runtime")
                self._has_credentials = True
                logger.info(f"Amazon Bedrock client initialized in region {self.region_name}")
            else:
                logger.info("No AWS credentials detected. Running in high-fidelity simulation mode.")
        except Exception as e:
            logger.warning(f"Bedrock client init note: {e}. Simulation mode active.")

    @property
    def is_live(self) -> bool:
        return self._has_credentials and self._client is not None

    async def converse_with_tools(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes an agent reasoning turn with Bedrock Converse API and tool definitions.
        Falls back smoothly to deterministic high-fidelity agent reasoning if Bedrock is offline.
        """
        if self.is_live:
            try:
                messages = list(conversation_history or [])
                messages.append({
                    "role": "user",
                    "content": [{"text": user_message}]
                })

                tool_config = {
                    "tools": BEDROCK_TOOL_SPECS,
                    "toolChoice": {"auto": {}}
                }

                response = self._client.converse(
                    modelId=self.model_id,
                    messages=messages,
                    system=[{"text": MASTER_PLANNER_SYSTEM_PROMPT}],
                    toolConfig=tool_config
                )

                output_message = response.get("output", {}).get("message", {})
                stop_reason = response.get("stopReason")
                usage = response.get("usage", {})

                # Extract tool calls if requested by the model
                tool_calls = []
                for content_block in output_message.get("content", []):
                    if "toolUse" in content_block:
                        t_use = content_block["toolUse"]
                        tool_calls.append({
                            "tool_use_id": t_use.get("toolUseId"),
                            "name": t_use.get("name"),
                            "arguments": t_use.get("input", {})
                        })

                return {
                    "mode": "live_bedrock",
                    "model": self.model_id,
                    "stop_reason": stop_reason,
                    "content": [b.get("text", "") for b in output_message.get("content", []) if "text" in b],
                    "tool_calls": tool_calls,
                    "usage": usage
                }

            except (ClientError, NoCredentialsError) as aws_err:
                logger.warning(f"AWS Bedrock call failed ({aws_err}). Falling back to simulation engine.")

        # High-Fidelity Simulation Execution
        return self._simulate_bedrock_agent_reasoning(user_message)

    def _simulate_bedrock_agent_reasoning(self, user_message: str) -> Dict[str, Any]:
        """
        Produces realistic, spec-accurate tool call plans and reasoning steps for testing
        and zero-credential demonstration.
        """
        msg_lower = user_message.lower()
        tool_calls = []

        # Step 1: Memory check if family/guests/dinner mentioned
        if any(w in msg_lower for w in ["parent", "mom", "dad", "family", "guest", "dinner", "visit"]):
            tool_calls.append({
                "tool_use_id": "call_bedrock_mem_01",
                "name": "household_memory_query_dietary",
                "arguments": {"member_name": "Mom"}
            })
            tool_calls.append({
                "tool_use_id": "call_bedrock_mem_02",
                "name": "household_memory_query_dietary",
                "arguments": {"member_name": "Dad"}
            })

        # Step 2: Culinary planning
        if any(w in msg_lower for w in ["dinner", "cook", "recipe", "food", "italian", "meal"]):
            tool_calls.append({
                "tool_use_id": "call_bedrock_cul_01",
                "name": "culinary_plan_menu",
                "arguments": {
                    "theme": "Gourmet Italian Dinner",
                    "dietary_restrictions": ["Strict Shellfish Allergy", "Gluten-Sensitive"],
                    "guest_count": 3,
                    "beverage_preference": "Chianti Classico"
                }
            })

        # Step 3: Amazon cart
        if any(w in msg_lower for w in ["order", "cart", "groceries", "buy", "dinner", "parent", "visit"]):
            tool_calls.append({
                "tool_use_id": "call_bedrock_cart_01",
                "name": "amazon_cart_assemble",
                "arguments": {
                    "ingredients": [
                        "Organic Gluten-Free Penne Rigate Pasta",
                        "San Marzano Whole Peeled Tomatoes DOP",
                        "Fresh Organic Basil Herb Bundle",
                        "Parmigiano Reggiano Aged 24 Months Wedge",
                        "Villa Antinori Chianti Classico Riserva 2019",
                        "Artisanal Gluten-Free Tiramisu Dessert"
                    ],
                    "delivery_window": "Friday 4:00 PM - 6:00 PM",
                    "dietary_filter": ["Gluten-Free"]
                }
            })

        # Step 4: Smart home ambiance
        if any(w in msg_lower for w in ["house", "light", "thermostat", "prepare", "music", "ambiance"]):
            tool_calls.append({
                "tool_use_id": "call_bedrock_iot_01",
                "name": "smart_ambiance_set_scene",
                "arguments": {
                    "scene_name": "Tuscan Sunset",
                    "target_temp_f": 71,
                    "color_temp_k": 2700,
                    "brightness_pct": 45,
                    "audio_theme": "Warm Acoustic Dinner Jazz",
                    "scheduled_for": "Friday 6:30 PM"
                }
            })

        # Step 5: Calendar coordination
        if any(w in msg_lower for w in ["weekend", "friday", "saturday", "calendar", "schedule", "brunch", "visit"]):
            tool_calls.append({
                "tool_use_id": "call_bedrock_cal_01",
                "name": "calendar_schedule_event",
                "arguments": {
                    "title": "Family Weekend Dinner & Welcome",
                    "start_time": "Friday 7:00 PM",
                    "end_time": "Friday 10:00 PM",
                    "attendees": ["Alex Henderson", "Mom (Elena)", "Dad (Robert)"]
                }
            })

        return {
            "mode": "high_fidelity_simulation",
            "model": "anthropic.claude-3-5-sonnet-20241022-v2:0 (Simulated)",
            "stop_reason": "tool_use",
            "content": [
                "Decomposing user goal into autonomous multi-service workflow. Querying household memory for safety restrictions, assembling certified groceries, configuring IoT atmosphere, and reserving the calendar."
            ],
            "tool_calls": tool_calls,
            "usage": {"inputTokens": 842, "outputTokens": 215, "totalTokens": 1057}
        }


bedrock_agent_client = BedrockAgentClient()
