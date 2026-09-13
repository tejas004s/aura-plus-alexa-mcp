"""
mcp_server.py - Self-Hosted MCP Server conforming to MCP Spec 2025-11-25+

Exposes Agent Skills, tools, resources, and prompts over Streamable HTTP and SSE.
"""

from typing import Dict, Any, List, Optional
import json
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from .schemas import (
    MCPRequest,
    MCPResponse,
    InitializeResult,
    MCPToolDefinition,
    MCPResourceDefinition,
    MCPPromptDefinition,
    ToolParamSchema
)
from .transports import transport_manager
from skills.household_memory import household_memory_skill
from skills.amazon_cart import amazon_cart_skill
from skills.smart_ambiance import smart_ambiance_skill
from skills.calendar_concierge import calendar_concierge_skill
from skills.culinary_planner import culinary_planner_skill

router = APIRouter(prefix="/mcp", tags=["MCP Server"])

# Tool Definitions conforming to MCP Schema
TOOLS_REGISTRY: Dict[str, MCPToolDefinition] = {
    "household_memory_get_summary": MCPToolDefinition(
        name="household_memory_get_summary",
        description="Retrieves the persistent household profile, family members, dietary rules, and connected devices.",
        inputSchema=ToolParamSchema(properties={})
    ),
    "household_memory_query_dietary": MCPToolDefinition(
        name="household_memory_query_dietary",
        description="Retrieves strict dietary restrictions, allergies, and food preferences for a specific household member.",
        inputSchema=ToolParamSchema(
            properties={
                "member_name": {"type": "string", "description": "Name or relation of the member, e.g., 'Mom', 'Elena', 'Dad'"}
            },
            required=["member_name"]
        )
    ),
    "household_memory_commit_preference": MCPToolDefinition(
        name="household_memory_commit_preference",
        description="Stores a newly learned preference or dietary constraint into long-term memory across sessions.",
        inputSchema=ToolParamSchema(
            properties={
                "member_name": {"type": "string", "description": "Target family member"},
                "preference": {"type": "string", "description": "The specific preference or fact learned"},
                "category": {"type": "string", "enum": ["preference", "allergy"], "description": "Category of fact"}
            },
            required=["member_name", "preference"]
        )
    ),
    "culinary_plan_menu": MCPToolDefinition(
        name="culinary_plan_menu",
        description="Plans an authentic multi-course gourmet menu strictly obeying allergies and dietary rules, including wine pairing and MCP App Carousel.",
        inputSchema=ToolParamSchema(
            properties={
                "theme": {"type": "string", "description": "Culinary theme, e.g., 'Italian Dinner Party'"},
                "dietary_restrictions": {"type": "array", "items": {"type": "string"}, "description": "List of allergies/rules to respect"},
                "guest_count": {"type": "integer", "description": "Number of attendees"},
                "beverage_preference": {"type": "string", "description": "Preferred wine style or beverage"}
            },
            required=["theme"]
        )
    ),
    "amazon_cart_assemble": MCPToolDefinition(
        name="amazon_cart_assemble",
        description="Autonomously searches Amazon Fresh catalog, verifies dietary tags, builds an itemized cart, and returns an interactive MCP App Checkout Card.",
        inputSchema=ToolParamSchema(
            properties={
                "ingredients": {"type": "array", "items": {"type": "string"}, "description": "List of recipe ingredients needed"},
                "delivery_window": {"type": "string", "description": "Preferred delivery time slot"},
                "dietary_filter": {"type": "array", "items": {"type": "string"}, "description": "Required certification tags, e.g., 'Gluten-Free'"}
            },
            required=["ingredients"]
        )
    ),
    "amazon_cart_approve_purchase": MCPToolDefinition(
        name="amazon_cart_approve_purchase",
        description="Executes human-authorized purchase of an assembled Amazon Fresh cart.",
        inputSchema=ToolParamSchema(
            properties={
                "cart_id": {"type": "string", "description": "Cart ID from amazon_cart_assemble"}
            },
            required=["cart_id"]
        )
    ),
    "smart_ambiance_set_scene": MCPToolDefinition(
        name="smart_ambiance_set_scene",
        description="Coordinates connected lighting scenes, color temperature (Kelvin), thermostat targets, and Amazon Music audio stream.",
        inputSchema=ToolParamSchema(
            properties={
                "scene_name": {"type": "string", "description": "Name of scene preset, e.g., 'Tuscan Sunset'"},
                "target_temp_f": {"type": "integer", "description": "Thermostat target in Fahrenheit"},
                "color_temp_k": {"type": "integer", "description": "Lighting color temp in Kelvin"},
                "brightness_pct": {"type": "integer", "description": "Lighting brightness 0-100"},
                "audio_theme": {"type": "string", "description": "Music playlist description"},
                "scheduled_for": {"type": "string", "description": "Time to activate, e.g., 'Friday 6:30 PM' or 'Now'"}
            }
        )
    ),
    "calendar_schedule_event": MCPToolDefinition(
        name="calendar_schedule_event",
        description="Schedules events on the household calendar, handles conflict detection, and generates interactive confirmation card.",
        inputSchema=ToolParamSchema(
            properties={
                "title": {"type": "string", "description": "Event title"},
                "start_time": {"type": "string", "description": "Start timestamp/string"},
                "end_time": {"type": "string", "description": "End timestamp/string"},
                "attendees": {"type": "array", "items": {"type": "string"}, "description": "Guest list"}
            },
            required=["title", "start_time", "end_time"]
        )
    ),
    "orchestrate_autonomous_concierge": MCPToolDefinition(
        name="orchestrate_autonomous_concierge",
        description="Master autonomous workflow: decomposes complex requests, audits memory, plans menu, prepares Amazon Cart, schedules ambiance, and sets calendar.",
        inputSchema=ToolParamSchema(
            properties={
                "user_prompt": {"type": "string", "description": "The high-level user instruction"}
            },
            required=["user_prompt"]
        )
    )
}

# MCP Resources
RESOURCES_REGISTRY: Dict[str, MCPResourceDefinition] = {
    "household://profile": MCPResourceDefinition(
        uri="household://profile",
        name="Household Profile & Family Member Registry",
        description="Active household profiles, allergies, and connected smart home devices."
    ),
    "amazon://fresh_catalog": MCPResourceDefinition(
        uri="amazon://fresh_catalog",
        name="Amazon Fresh Available Pantry Catalog",
        description="Live items, pricing, inventory status, and certified dietary flags."
    ),
    "smart_home://active_scene": MCPResourceDefinition(
        uri="smart_home://active_scene",
        name="Smart Home Live Environment State",
        description="Current thermostat readings, lighting Kelvin, and audio queue."
    )
}

# MCP Prompts
PROMPTS_REGISTRY: Dict[str, MCPPromptDefinition] = {
    "prepare_family_weekend": MCPPromptDefinition(
        name="prepare_family_weekend",
        description="Autonomous concierge workflow to prepare the household for visiting family members.",
        arguments=[{"name": "guests", "description": "Names of visiting guests", "required": True}]
    )
}


async def execute_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatches tool calls to the corresponding Agent Skill."""
    if name == "household_memory_get_summary":
        return household_memory_skill.get_household_summary()
    elif name == "household_memory_query_dietary":
        return household_memory_skill.query_member_dietary(arguments.get("member_name", ""))
    elif name == "household_memory_commit_preference":
        return household_memory_skill.remember_preference(
            member_name=arguments.get("member_name", ""),
            preference_or_fact=arguments.get("preference", ""),
            category=arguments.get("category", "preference")
        )
    elif name == "culinary_plan_menu":
        return culinary_planner_skill.plan_menu(
            theme=arguments.get("theme", "Italian Dinner Party"),
            dietary_restrictions=arguments.get("dietary_restrictions"),
            guest_count=arguments.get("guest_count", 3),
            beverage_preference=arguments.get("beverage_preference", "Chianti Classico")
        )
    elif name == "amazon_cart_assemble":
        return amazon_cart_skill.build_cart_for_menu(
            ingredients=arguments.get("ingredients", []),
            delivery_window=arguments.get("delivery_window", "Friday 4:00 PM - 6:00 PM"),
            dietary_requirements=arguments.get("dietary_filter")
        )
    elif name == "amazon_cart_approve_purchase":
        return amazon_cart_skill.execute_purchase_approval(arguments.get("cart_id", ""))
    elif name == "smart_ambiance_set_scene":
        return smart_ambiance_skill.configure_scene(
            scene_name=arguments.get("scene_name", "Tuscan Sunset"),
            target_temp_f=arguments.get("target_temp_f", 71),
            color_temp_k=arguments.get("color_temp_k", 2700),
            brightness_pct=arguments.get("brightness_pct", 45),
            audio_theme=arguments.get("audio_theme", "Warm Acoustic Dinner Jazz"),
            scheduled_for=arguments.get("scheduled_for", "Friday 6:30 PM")
        )
    elif name == "calendar_schedule_event":
        return calendar_concierge_skill.schedule_event(
            title=arguments.get("title", ""),
            start_time=arguments.get("start_time", ""),
            end_time=arguments.get("end_time", ""),
            attendees=arguments.get("attendees")
        )
    elif name == "orchestrate_autonomous_concierge":
        # Import lazily to avoid circular imports with orchestrator
        from aws_orchestrator.agent_core import agent_core_orchestrator
        return await agent_core_orchestrator.process_request(arguments.get("user_prompt", ""))
    else:
        raise ValueError(f"Unknown MCP tool: '{name}'")


@router.get("/sse")
async def sse_endpoint(request: Request):
    """
    Streamable HTTP SSE Transport entry point.
    Initializes a new SSE session and returns the message endpoint to the client.
    """
    session_id = transport_manager.create_session()
    return EventSourceResponse(transport_manager.sse_event_stream(session_id, request))


@router.post("/message")
async def mcp_message_handler(request: Request, session_id: Optional[str] = Query(None)):
    """
    Processes incoming MCP JSON-RPC 2.0 requests over HTTP.
    Returns response directly and/or streams updates to the SSE session.
    """
    try:
        body = await request.json()
        mcp_req = MCPRequest(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid MCP JSON-RPC request: {str(e)}")

    method = mcp_req.method
    req_id = mcp_req.id
    params = mcp_req.params or {}

    response_data = None
    error_data = None

    try:
        if method == "initialize":
            response_data = InitializeResult().model_dump()

        elif method == "tools/list":
            tools_list = [tool.model_dump() for tool in TOOLS_REGISTRY.values()]
            response_data = {"tools": tools_list}

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            if tool_name not in TOOLS_REGISTRY:
                error_data = {"code": -32601, "message": f"Tool '{tool_name}' not found."}
            else:
                call_result = await execute_tool_call(tool_name, tool_args)
                response_data = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(call_result, indent=2)
                        }
                    ]
                }

        elif method == "resources/list":
            res_list = [res.model_dump() for res in RESOURCES_REGISTRY.values()]
            response_data = {"resources": res_list}

        elif method == "resources/read":
            uri = params.get("uri")
            if uri == "household://profile":
                content = household_memory_skill.get_household_summary()
            elif uri == "amazon://fresh_catalog":
                content = amazon_cart_skill.search_products("")
            elif uri == "smart_home://active_scene":
                content = smart_ambiance_skill.get_current_state()
            else:
                raise ValueError(f"Resource uri '{uri}' not found.")
            response_data = {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(content, indent=2)
                    }
                ]
            }

        elif method == "prompts/list":
            prompts_list = [p.model_dump() for p in PROMPTS_REGISTRY.values()]
            response_data = {"prompts": prompts_list}

        else:
            error_data = {"code": -32601, "message": f"Method '{method}' not implemented."}

    except Exception as err:
        error_data = {"code": -32000, "message": str(err)}

    mcp_resp = MCPResponse(
        id=req_id,
        result=response_data if not error_data else None,
        error=error_data
    )

    # If SSE session is connected, stream the response event
    if session_id:
        await transport_manager.broadcast_event(session_id, "message", mcp_resp.model_dump())

    return JSONResponse(content=mcp_resp.model_dump())
