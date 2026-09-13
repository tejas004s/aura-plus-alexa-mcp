"""
test_skills.py - Unit tests for Alexa+ Agent Skills
"""

import pytest
from skills.household_memory import household_memory_skill
from skills.amazon_cart import amazon_cart_skill
from skills.smart_ambiance import smart_ambiance_skill
from skills.calendar_concierge import calendar_concierge_skill
from skills.culinary_planner import culinary_planner_skill


def test_household_memory():
    summary = household_memory_skill.get_household_summary()
    assert "members" in summary
    assert len(summary["members"]) > 0

    mom_diet = household_memory_skill.query_member_dietary("Mom")
    assert mom_diet["found"] is True
    assert any("shellfish" in r.lower() for r in mom_diet["dietary_restrictions"])
    assert any("gluten" in r.lower() for r in mom_diet["dietary_restrictions"])


def test_culinary_planner():
    menu = culinary_planner_skill.plan_menu(
        theme="Italian Dinner Party",
        dietary_restrictions=["Strict Shellfish Allergy", "Gluten-Sensitive"],
        guest_count=3
    )
    assert menu["dietary_verified"] is True
    assert len(menu["courses"]) >= 3
    assert "mcp_app_carousel" in menu
    assert menu["mcp_app_carousel"]["component"] == "MCPAppCarousel"


def test_amazon_cart():
    items = ["Organic Gluten-Free Penne Rigate Pasta", "San Marzano Whole Peeled Tomatoes DOP"]
    cart_res = amazon_cart_skill.build_cart_for_menu(items, dietary_requirements=["Gluten-Free"])
    assert "cart_summary" in cart_res
    assert len(cart_res["cart_summary"]["items"]) > 0
    assert cart_res["cart_summary"]["total"] > 0
    assert "mcp_app_card" in cart_res
    assert cart_res["mcp_app_card"]["type"] == "amazon_fresh_checkout"


def test_smart_ambiance():
    scene = smart_ambiance_skill.configure_scene("Tuscan Sunset", target_temp_f=71, color_temp_k=2700)
    assert scene["ambiance_state"]["climate"]["target_temp_f"] == 71
    assert scene["ambiance_state"]["lighting"]["color_temp_k"] == 2700
    assert "mcp_app_card" in scene


def test_calendar_concierge():
    evt = calendar_concierge_skill.schedule_event(
        title="Family Welcome Dinner",
        start_time="Friday 7:00 PM",
        end_time="Friday 10:00 PM"
    )
    assert evt["event"]["status"] == "confirmed"
    assert "mcp_app_card" in evt
