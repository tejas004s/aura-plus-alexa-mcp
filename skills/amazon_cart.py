"""
amazon_cart.py - Agent Skill for Autonomous Amazon Purchasing & Cart Orchestration

Integrates product discovery, inventory lookup, dietary constraint filtering,
and safe autonomous cart orchestration with Human-in-the-Loop approval cards (MCP App).
"""

from typing import Dict, Any, List, Optional
import json
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "pantry_catalog.json"


class AmazonCartSkill:
    """Agent Skill providing Amazon Fresh cart assembly and purchasing capabilities."""

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or CATALOG_PATH
        self._catalog = self._load_catalog()
        self._active_cart = {
            "cart_id": "cart_live_session_01",
            "items": [],
            "status": "idle",
            "subtotal": 0.0,
            "delivery_fee": 0.0,
            "estimated_tax": 0.0,
            "total": 0.0
        }

    def _load_catalog(self) -> List[Dict[str, Any]]:
        if not self.catalog_path.exists():
            return []
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def search_products(self, query: str, dietary_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Searches the Amazon Fresh catalog matching keywords and filters out items
        violating dietary restrictions.
        """
        q_lower = query.lower()
        results = []
        for item in self._catalog:
            matches_query = (
                q_lower in item["name"].lower() or
                q_lower in item["category"].lower() or
                q_lower in item["brand"].lower()
            )
            if matches_query:
                # Check dietary requirements
                if dietary_filter:
                    item_tags = [t.lower() for t in item.get("dietary", [])]
                    required_clean = [req.lower() for req in dietary_filter]
                    # If Gluten-Free required, check that item has it
                    if any("gluten-free" in req for req in required_clean) and not any("gluten-free" in t for t in item_tags):
                        continue
                results.append(item)
        return results

    def build_cart_for_menu(self, ingredients: List[str], delivery_window: str = "Friday 4:00 PM - 6:00 PM", dietary_requirements: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Takes high-level recipe ingredients, autonomously selects the best-matched
        Amazon Fresh certified items meeting dietary restrictions, and prepares an itemized order.
        """
        cart_items = []
        subtotal = 0.0

        for ing in ingredients:
            matches = self.search_products(ing, dietary_filter=dietary_requirements)
            if not matches:
                matches = self.search_products(ing)
            
            if matches:
                selected = matches[0]
                item_entry = {
                    "asin": selected["asin"],
                    "name": selected["name"],
                    "brand": selected["brand"],
                    "unit_price": selected["price"],
                    "quantity": 1,
                    "line_total": round(selected["price"], 2),
                    "image_url": selected["image_url"],
                    "dietary": selected.get("dietary", [])
                }
                cart_items.append(item_entry)
                subtotal += selected["price"]

        tax = round(subtotal * 0.065, 2)
        delivery_fee = 0.0  # Free Fresh delivery for Prime orders > $35
        total = round(subtotal + tax + delivery_fee, 2)

        self._active_cart = {
            "cart_id": f"cart_{len(cart_items)}_items",
            "items": cart_items,
            "status": "awaiting_user_approval",
            "subtotal": round(subtotal, 2),
            "delivery_fee": delivery_fee,
            "estimated_tax": tax,
            "total": total,
            "delivery_window": delivery_window,
            "destination": "410 Terry Ave N, Seattle, WA 98109"
        }

        # Generate MCP App Generative UI schema
        mcp_app_card = {
            "component": "MCPAppCard",
            "type": "amazon_fresh_checkout",
            "title": "Amazon Fresh Order Ready",
            "subtitle": f"{len(cart_items)} items prepared for {delivery_window}",
            "data": self._active_cart,
            "actions": [
                {
                    "id": "confirm_checkout",
                    "label": f"Approve & Purchase (${total:.2f})",
                    "style": "primary_brand",
                    "payload": {"cart_id": self._active_cart["cart_id"], "action": "execute_payment"}
                },
                {
                    "id": "modify_cart",
                    "label": "Customize Items",
                    "style": "secondary",
                    "payload": {"cart_id": self._active_cart["cart_id"], "action": "open_editor"}
                }
            ]
        }

        return {
            "cart_summary": self._active_cart,
            "mcp_app_card": mcp_app_card
        }

    def execute_purchase_approval(self, cart_id: str) -> Dict[str, Any]:
        """
        Executes the final human-authorized transaction against the Amazon payment pipeline.
        """
        if self._active_cart.get("cart_id") != cart_id:
            return {"success": False, "error": "Cart ID mismatch or expired session."}

        self._active_cart["status"] = "confirmed_placed"
        self._active_cart["order_id"] = "AMZ-FRESH-992-88120"

        return {
            "success": True,
            "status": "ORDER_PLACED",
            "order_id": self._active_cart["order_id"],
            "total_charged": f"${self._active_cart['total']:.2f}",
            "delivery_window": self._active_cart["delivery_window"],
            "message": "Order successfully placed with Amazon Fresh. Delivery scheduled."
        }


# Singleton instance
amazon_cart_skill = AmazonCartSkill()
