"""
main.py - Aura+ Alexa+ Multi-Modal Application & MCP Server

Main server entry point combining:
1. Self-Hosted MCP Server (Spec 2025-11-25+ over Streamable HTTP)
2. Interactive Alexa+ Web Simulator & MCP Apps Engine
3. AWS Bedrock & AgentCore Orchestrator API
"""

import os
import json
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from server.mcp_server import router as mcp_router
from aws_orchestrator.agent_core import agent_core_orchestrator
from skills.household_memory import household_memory_skill
from skills.amazon_cart import amazon_cart_skill
from skills.smart_ambiance import smart_ambiance_skill
from skills.calendar_concierge import calendar_concierge_skill

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Aura+ | Autonomous Alexa+ Concierge",
    description="Winning Submission for Amazon Developer Hackathon (Alexa+ Track & AWS Builder Mini Challenge)",
    version="1.0.0"
)

SERVER_START_TIME = time.time()

# Enable CORS for developer tools & MCP clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount MCP Protocol Router
app.include_router(mcp_router)

# Mount Static Files & Templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "mcp_spec": "2025-11-25",
        "uptime_seconds": time.time() - SERVER_START_TIME
    }


@app.get("/", response_class=HTMLResponse)
async def home_view(request: Request):
    """Renders the Alexa+ Simulated Multi-Modal Experience."""
    household = household_memory_skill.get_household_summary()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "household": household,
            "connected_devices": household.get("connected_devices", [])
        }
    )


@app.post("/api/converse")
async def converse_api(request: Request):
    """
    Main conversational agent endpoint.
    Receives user prompt (from voice transcription or text), executes the AWS Bedrock / AgentCore
    multi-agent workflow, and returns voice synthesis text, MCP Apps UI, and execution traces.
    """
    body = await request.json()
    prompt = body.get("prompt", "").strip()
    if not prompt:
        return JSONResponse(status_code=400, content={"error": "Prompt cannot be empty."})

    result = await agent_core_orchestrator.process_request(prompt)
    return JSONResponse(content=result)


@app.get("/api/memory")
async def get_memory():
    """Retrieves current household memory state."""
    return JSONResponse(content=household_memory_skill.get_household_summary())


@app.post("/api/memory/remember")
async def remember_preference(request: Request):
    """Allows adding/modifying persistent preferences across sessions."""
    body = await request.json()
    member = body.get("member_name", "Alex")
    preference = body.get("preference", "")
    category = body.get("category", "preference")
    res = household_memory_skill.remember_preference(member, preference, category)
    return JSONResponse(content=res)


@app.post("/api/cart/approve")
async def approve_cart(request: Request):
    """Executes Human-in-the-Loop purchase approval for Amazon Fresh cart."""
    body = await request.json()
    cart_id = body.get("cart_id", "")
    res = amazon_cart_skill.execute_purchase_approval(cart_id)
    return JSONResponse(content=res)


@app.post("/api/ambiance/update")
async def update_ambiance(request: Request):
    """Handles real-time adjustments from interactive MCP App Ambiance sliders."""
    body = await request.json()
    res = smart_ambiance_skill.configure_scene(
        scene_name=body.get("scene_name", "Tuscan Sunset"),
        target_temp_f=int(body.get("target_temp_f", 71)),
        brightness_pct=int(body.get("brightness_pct", 45)),
        scheduled_for=body.get("scheduled_for", "Now")
    )
    return JSONResponse(content=res)


@app.get("/health")
async def health_check():
    """Production health check endpoint for container orchestrators and monitoring."""
    from aws_orchestrator.sustainability import resource_tracker
    return JSONResponse(content={
        "status": "healthy",
        "version": "1.0.0",
        "mcp_spec": "2025-11-25",
        "uptime_seconds": round(time.time() - SERVER_START_TIME, 1),
        "sustainability": resource_tracker.get_session_metrics()
    })


@app.get("/api/sustainability")
async def sustainability_report():
    """Returns current session environmental impact metrics and optimization suggestions."""
    from aws_orchestrator.sustainability import resource_tracker
    return JSONResponse(content=resource_tracker.get_efficiency_report())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
