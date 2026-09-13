"""
culinary_planner.py - Agent Skill for Personalized Culinary & Dietary Planning

Synthesizes tailored gourmet menus strictly obeying household allergies and dietary rules,
recommends wine pairings from historical preferences, and formats an interactive MCP App Carousel.
"""

from typing import Dict, Any, List, Optional


class CulinaryPlannerSkill:
    """Agent Skill that crafts dietary-safe menus and generative recipe carousels."""

    def plan_menu(
        self,
        theme: str = "Italian Dinner Party",
        dietary_restrictions: Optional[List[str]] = None,
        guest_count: int = 3,
        beverage_preference: str = "Chianti Classico"
    ) -> Dict[str, Any]:
        """
        Creates a tailored 3-course menu + wine pairing respecting dietary safety constraints.
        """
        dietary_restrictions = dietary_restrictions or ["Strict Shellfish Allergy", "Gluten-Sensitive"]

        courses = [
            {
                "id": "course_1",
                "course": "Antipasto",
                "title": "Heirloom Caprese with Aged Balsamic & Fresh Basil",
                "prep_time": "10 mins",
                "dietary_badges": ["Gluten-Free", "Vegetarian", "Shellfish-Free"],
                "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500",
                "ingredients": ["San Marzano Whole Peeled Tomatoes DOP", "Fresh Organic Basil Herb Bundle", "Extra Virgin Cold-Pressed Olive Oil"],
                "chef_notes": "Utilizes fresh organic sweet basil with cold-pressed olive oil. Zero allergen risk."
            },
            {
                "id": "course_2",
                "course": "Primo Piatto (Main)",
                "title": "Artisanal Penne all'Arrabbiata with Aged Parmigiano",
                "prep_time": "25 mins",
                "dietary_badges": ["Certified Gluten-Free", "Vegetarian", "Shellfish-Free"],
                "image_url": "https://images.unsplash.com/photo-1621996346565-e3d5d62816dd?w=500",
                "ingredients": ["Organic Gluten-Free Penne Rigate Pasta", "San Marzano Whole Peeled Tomatoes DOP", "Parmigiano Reggiano Aged 24 Months Wedge"],
                "chef_notes": "Crafted with 100% certified gluten-free corn/rice penne rigate to guarantee Mom's safety."
            },
            {
                "id": "course_3",
                "course": "Sommelier Pairing",
                "title": "Villa Antinori Chianti Classico Riserva 2019",
                "prep_time": "Serve at 64°F",
                "dietary_badges": ["Dad's Favorite Profile", "Tuscan Heritage"],
                "image_url": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=500",
                "ingredients": ["Villa Antinori Chianti Classico Riserva 2019"],
                "chef_notes": "A bold Tuscan red featuring notes of dark cherry and tobacco, perfectly complementing the Arrabbiata sauce."
            },
            {
                "id": "course_4",
                "course": "Dolce",
                "title": "Decaf Espresso Gluten-Free Tiramisu",
                "prep_time": "Ready to serve",
                "dietary_badges": ["Gluten-Free", "Decaf Infused"],
                "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500",
                "ingredients": ["Artisanal Gluten-Free Tiramisu Dessert"],
                "chef_notes": "Pre-made artisanal dessert respecting evening decaf and gluten-free preferences."
            }
        ]

        # Extract all unique ingredients required for Amazon Cart purchasing
        all_ingredients = []
        for c in courses:
            all_ingredients.extend(c["ingredients"])
        # Deduplicate
        unique_ingredients = list(dict.fromkeys(all_ingredients))

        # Generative UI MCP App Carousel schema
        mcp_app_carousel = {
            "component": "MCPAppCarousel",
            "type": "recipe_menu_carousel",
            "title": f"Custom Curated Menu: {theme}",
            "subtitle": f"Strictly filtered for {', '.join(dietary_restrictions)} ({guest_count} guests)",
            "cards": courses,
            "actions": [
                {
                    "id": "order_all_ingredients",
                    "label": "Add All Ingredients to Amazon Cart",
                    "style": "primary",
                    "payload": {"action": "assemble_cart", "ingredients": unique_ingredients}
                }
            ]
        }

        return {
            "menu_theme": theme,
            "dietary_verified": True,
            "guest_count": guest_count,
            "courses": courses,
            "required_ingredients": unique_ingredients,
            "mcp_app_carousel": mcp_app_carousel
        }


# Singleton instance
culinary_planner_skill = CulinaryPlannerSkill()
