"""
prompts.py - System Prompts and AWS Bedrock Tool Specifications

Implements multi-agent reasoning prompts following the AWS AgentCore / Strands pattern.
"""

from typing import List, Dict, Any

MASTER_PLANNER_SYSTEM_PROMPT = """You are Aura+, an autonomous, context-aware household and executive concierge powered by Alexa+ and AWS Bedrock.
Your objective is to autonomously orchestrate multi-step real-world workflows for the user by delegating to specialized Agent Skills via the Model Context Protocol (MCP).

GUIDING PRINCIPLES:
1. SAFETY FIRST: Always query household memory for allergies and dietary restrictions before recommending or purchasing food. Never violate documented allergies.
2. AUTONOMOUS BUT RESPECTFUL: Prepare cart orders and IoT scenes automatically, but require Human-in-the-Loop confirmation for financial purchases above $0.
3. MULTI-MODAL GENERATIVE UI: Structure responses with interactive cards, carousels, and visual widgets (MCP Apps) alongside concise, natural spoken voice responses.
4. PROACTIVE COORDINATION: When a major event is planned (e.g. guests visiting), coordinate all dimensions: meal planning, grocery procurement, ambiance scenes, and calendar scheduling.
"""

BEDROCK_TOOL_SPECS: List[Dict[str, Any]] = [
    {
        "toolSpec": {
            "name": "household_memory_query_dietary",
            "description": "Retrieves dietary restrictions, strict allergies, and culinary preferences for household members or guests.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "member_name": {
                            "type": "string",
                            "description": "Name or relation of the household member (e.g., 'Mom', 'Elena', 'Dad')"
                        }
                    },
                    "required": ["member_name"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "culinary_plan_menu",
            "description": "Plans a gourmet multi-course dinner menu strictly filtered by allergies and dietary restrictions, with wine pairings and recipe cards.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "theme": {"type": "string", "description": "Menu theme or style"},
                        "dietary_restrictions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Allergies and restrictions to enforce"
                        },
                        "guest_count": {"type": "integer", "description": "Number of diners"},
                        "beverage_preference": {"type": "string", "description": "Wine or drink style"}
                    },
                    "required": ["theme"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "amazon_cart_assemble",
            "description": "Searches Amazon Fresh inventory, selects dietary-verified ingredients, and builds an itemized checkout card for approval.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "ingredients": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of required ingredients"
                        },
                        "delivery_window": {"type": "string", "description": "Delivery time slot"},
                        "dietary_filter": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Dietary filters like Gluten-Free"
                        }
                    },
                    "required": ["ingredients"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "smart_ambiance_set_scene",
            "description": "Configures connected lighting scenes, color temperature, thermostat, and music stream for the event.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "scene_name": {"type": "string", "description": "Name of preset scene"},
                        "target_temp_f": {"type": "integer", "description": "Thermostat target in Fahrenheit"},
                        "color_temp_k": {"type": "integer", "description": "Color temperature in Kelvin"},
                        "brightness_pct": {"type": "integer", "description": "Brightness percentage 1-100"},
                        "audio_theme": {"type": "string", "description": "Music playlist description"},
                        "scheduled_for": {"type": "string", "description": "Scheduled activation time"}
                    }
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "calendar_schedule_event",
            "description": "Schedules the dinner or family event in the household calendar with reminders.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Event title"},
                        "start_time": {"type": "string", "description": "Start time"},
                        "end_time": {"type": "string", "description": "End time"},
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of attendees"
                        }
                    },
                    "required": ["title", "start_time", "end_time"]
                }
            }
        }
    }
]
