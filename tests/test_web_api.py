"""
test_web_api.py - Integration tests for Web Simulator endpoints
"""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_home_page():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        assert "Aura+" in res.text
        assert "alexa-orb" in res.text


@pytest.mark.asyncio
async def test_converse_api_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "prompt": "My parents are visiting this Friday evening. Prepare dinner and set the ambiance."
        }
        res = await ac.post("/api/converse", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "spoken_response" in data
        assert "execution_trace" in data
        assert len(data["mcp_apps"]) >= 3


@pytest.mark.asyncio
async def test_cart_approve_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First assemble cart
        conv = await ac.post("/api/converse", json={"prompt": "Order groceries for Italian dinner"})
        data = conv.json()
        cart_id = "cart_6_items"
        for app_widget in data.get("mcp_apps", []):
            if app_widget.get("type") == "amazon_fresh_checkout":
                cart_id = app_widget.get("data", {}).get("cart_id", cart_id)

        res = await ac.post("/api/cart/approve", json={"cart_id": cart_id})
        assert res.status_code == 200
        result = res.json()
        assert result["success"] is True
        assert "order_id" in result


@pytest.mark.asyncio
async def test_ambiance_update_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "scene_name": "Tuscan Sunset",
            "target_temp_f": 72,
            "brightness_pct": 50
        }
        res = await ac.post("/api/ambiance/update", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["ambiance_state"]["climate"]["target_temp_f"] == 72
