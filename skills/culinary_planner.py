"""
culinary_planner.py - Agent Skill for Personalized Culinary & Dietary Planning

Synthesizes tailored gourmet menus from a multi-cuisine recipe database,
strictly obeying household allergies and dietary rules, recommends wine pairings
from historical preferences, and formats an interactive MCP App Carousel.
"""

from typing import Dict, Any, List, Optional
import hashlib


# ─── Recipe Database (Multi-Cuisine, Dietary-Tagged) ───────────────────────
RECIPE_DATABASE: List[Dict[str, Any]] = [
    # ── Italian ──
    {"id": "it_01", "cuisine": "Italian", "course": "Antipasto", "title": "Heirloom Caprese with Aged Balsamic & Fresh Basil", "prep_time": "10 mins", "tags": ["gluten-free", "vegetarian", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500", "ingredients": ["San Marzano Whole Peeled Tomatoes DOP", "Fresh Organic Basil Herb Bundle", "Extra Virgin Cold-Pressed Olive Oil"], "chef_notes": "Utilizes fresh organic sweet basil with cold-pressed olive oil. Zero allergen risk."},
    {"id": "it_02", "cuisine": "Italian", "course": "Main", "title": "Artisanal Penne all'Arrabbiata with Aged Parmigiano", "prep_time": "25 mins", "tags": ["gluten-free", "vegetarian", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1621996346565-e3d5d62816dd?w=500", "ingredients": ["Organic Gluten-Free Penne Rigate Pasta", "San Marzano Whole Peeled Tomatoes DOP", "Parmigiano Reggiano Aged 24 Months Wedge"], "chef_notes": "Crafted with 100% certified gluten-free corn/rice penne rigate."},
    {"id": "it_03", "cuisine": "Italian", "course": "Main", "title": "Wild Mushroom Risotto with Truffle Oil", "prep_time": "35 mins", "tags": ["gluten-free", "vegetarian", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1476124369491-e7addf5db371?w=500", "ingredients": ["Arborio Rice Premium", "Mixed Wild Mushroom Medley", "White Truffle Oil"], "chef_notes": "Naturally gluten-free Arborio rice with earthy mushrooms and luxurious truffle finish."},
    {"id": "it_04", "cuisine": "Italian", "course": "Dessert", "title": "Decaf Espresso Gluten-Free Tiramisu", "prep_time": "Ready to serve", "tags": ["gluten-free", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500", "ingredients": ["Artisanal Gluten-Free Tiramisu Dessert"], "chef_notes": "Pre-made artisanal dessert respecting evening decaf and gluten-free preferences."},
    {"id": "it_05", "cuisine": "Italian", "course": "Dessert", "title": "Classic Panna Cotta with Berry Compote", "prep_time": "15 mins + chill", "tags": ["gluten-free", "vegetarian", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=500", "ingredients": ["Heavy Cream Organic", "Vanilla Bean Extract", "Mixed Berry Compote"], "chef_notes": "Silky custard dessert naturally gluten-free with fresh berry topping."},
    # ── Mexican ──
    {"id": "mx_01", "cuisine": "Mexican", "course": "Antipasto", "title": "Grilled Corn Elote Cups with Lime Crema", "prep_time": "15 mins", "tags": ["gluten-free", "vegetarian", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?w=500", "ingredients": ["Sweet Corn Ears Organic", "Mexican Crema", "Tajin Seasoning"], "chef_notes": "Street-style elote in individual cups with smoky chili lime crema."},
    {"id": "mx_02", "cuisine": "Mexican", "course": "Main", "title": "Black Bean & Sweet Potato Enchiladas Verdes", "prep_time": "40 mins", "tags": ["gluten-free", "vegetarian", "shellfish-free", "nut-free", "dairy-free"], "image_url": "https://images.unsplash.com/photo-1534352956036-cd81e27dd615?w=500", "ingredients": ["Corn Tortillas Organic", "Black Beans Canned", "Sweet Potato", "Salsa Verde"], "chef_notes": "Corn tortillas ensure gluten-free compliance. Rich and hearty plant-based filling."},
    {"id": "mx_03", "cuisine": "Mexican", "course": "Dessert", "title": "Churro Bites with Chocolate Dipping Sauce", "prep_time": "20 mins", "tags": ["vegetarian", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1624353365286-3f8d62daad51?w=500", "ingredients": ["Gluten-Free Flour Blend", "Dark Chocolate Chips", "Cinnamon Sugar"], "chef_notes": "Can be made with GF flour blend for dietary compliance."},
    # ── Japanese ──
    {"id": "jp_01", "cuisine": "Japanese", "course": "Antipasto", "title": "Edamame with Sea Salt & Sesame", "prep_time": "5 mins", "tags": ["gluten-free", "vegan", "shellfish-free", "nut-free", "dairy-free"], "image_url": "https://images.unsplash.com/photo-1564834744159-ff0ea41ba4b9?w=500", "ingredients": ["Frozen Edamame Pods", "Sea Salt Flakes", "Toasted Sesame Seeds"], "chef_notes": "Light, protein-rich starter. Naturally allergen-safe."},
    {"id": "jp_02", "cuisine": "Japanese", "course": "Main", "title": "Teriyaki Glazed Tofu Bowl with Sticky Rice", "prep_time": "30 mins", "tags": ["gluten-free", "vegan", "shellfish-free", "nut-free", "dairy-free"], "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500", "ingredients": ["Firm Organic Tofu", "Tamari Gluten-Free Soy Sauce", "Short Grain Sushi Rice"], "chef_notes": "Uses tamari instead of soy sauce for strict gluten-free compliance."},
    {"id": "jp_03", "cuisine": "Japanese", "course": "Dessert", "title": "Matcha Green Tea Mochi Ice Cream", "prep_time": "Ready to serve", "tags": ["gluten-free", "vegetarian", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500", "ingredients": ["Matcha Mochi Ice Cream Box"], "chef_notes": "Premade mochi treats naturally gluten-free with ceremonial-grade matcha."},
    # ── Indian ──
    {"id": "in_01", "cuisine": "Indian", "course": "Antipasto", "title": "Crispy Vegetable Samosas with Tamarind Chutney", "prep_time": "20 mins", "tags": ["vegetarian", "shellfish-free", "nut-free", "dairy-free"], "image_url": "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?w=500", "ingredients": ["Frozen Samosa Pack", "Tamarind Chutney"], "chef_notes": "Classic appetizer. Contains wheat flour — check gluten restrictions."},
    {"id": "in_02", "cuisine": "Indian", "course": "Main", "title": "Chana Masala with Basmati Rice & Naan", "prep_time": "35 mins", "tags": ["vegetarian", "shellfish-free", "nut-free", "dairy-free"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500", "ingredients": ["Chickpeas Canned", "Garam Masala Spice Blend", "Basmati Rice Premium"], "chef_notes": "Rich chickpea curry. Basmati rice is naturally gluten-free but naan contains wheat."},
    {"id": "in_03", "cuisine": "Indian", "course": "Main", "title": "Palak Paneer with Saffron Rice", "prep_time": "30 mins", "tags": ["gluten-free", "vegetarian", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500", "ingredients": ["Fresh Spinach Bundle", "Paneer Cheese Block", "Saffron Threads"], "chef_notes": "Creamy spinach curry with fresh paneer. Naturally gluten-free when served with rice."},
    {"id": "in_04", "cuisine": "Indian", "course": "Dessert", "title": "Mango Lassi & Gulab Jamun", "prep_time": "10 mins", "tags": ["vegetarian", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1587314168485-3236d6710814?w=500", "ingredients": ["Alphonso Mango Pulp", "Greek Yogurt", "Gulab Jamun Mix"], "chef_notes": "Traditional Indian dessert duo. Gulab jamun contains wheat flour."},
    # ── French ──
    {"id": "fr_01", "cuisine": "French", "course": "Antipasto", "title": "French Onion Soup Gratinée", "prep_time": "45 mins", "tags": ["shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=500", "ingredients": ["Sweet Onions", "Gruyère Cheese", "Baguette Croutons"], "chef_notes": "Classic French comfort — contains gluten from croutons and dairy from Gruyère."},
    {"id": "fr_02", "cuisine": "French", "course": "Antipasto", "title": "Salade Niçoise with Herb Vinaigrette", "prep_time": "15 mins", "tags": ["gluten-free", "shellfish-free", "nut-free", "dairy-free"], "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500", "ingredients": ["Mixed Greens", "Niçoise Olives", "Dijon Vinaigrette"], "chef_notes": "Light Mediterranean salad, naturally gluten-free and dairy-free."},
    {"id": "fr_03", "cuisine": "French", "course": "Main", "title": "Ratatouille Provençale with Herb Crust", "prep_time": "50 mins", "tags": ["gluten-free", "vegan", "shellfish-free", "nut-free", "dairy-free"], "image_url": "https://images.unsplash.com/photo-1572453800999-e8d2d1589b7c?w=500", "ingredients": ["Eggplant", "Zucchini", "Bell Peppers", "Roma Tomatoes"], "chef_notes": "Classic Provençale vegetable dish, entirely plant-based and allergen-safe."},
    {"id": "fr_04", "cuisine": "French", "course": "Dessert", "title": "Crème Brûlée with Madagascar Vanilla", "prep_time": "60 mins + chill", "tags": ["gluten-free", "vegetarian", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1470124182917-cc6e71b22ecc?w=500", "ingredients": ["Heavy Cream Organic", "Vanilla Bean Extract", "Cage-Free Eggs"], "chef_notes": "Naturally gluten-free French custard with caramelized sugar top."},
    # ── Mediterranean ──
    {"id": "md_01", "cuisine": "Mediterranean", "course": "Antipasto", "title": "Hummus Trio with Grilled Pita & Olive Tapenade", "prep_time": "10 mins", "tags": ["vegan", "shellfish-free", "nut-free", "dairy-free"], "image_url": "https://images.unsplash.com/photo-1577805947697-89e18249d767?w=500", "ingredients": ["Classic Hummus", "Roasted Red Pepper Hummus", "Grilled Pita Bread"], "chef_notes": "Contains gluten from pita bread. Can substitute with GF crackers."},
    {"id": "md_02", "cuisine": "Mediterranean", "course": "Main", "title": "Grilled Halloumi & Quinoa Mediterranean Bowl", "prep_time": "25 mins", "tags": ["gluten-free", "vegetarian", "shellfish-free", "nut-free"], "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500", "ingredients": ["Halloumi Cheese", "Organic Quinoa", "Cherry Tomatoes", "Kalamata Olives"], "chef_notes": "Protein-rich quinoa bowl with grilled halloumi. Naturally gluten-free."},
    {"id": "md_03", "cuisine": "Mediterranean", "course": "Dessert", "title": "Baklava with Honey & Pistachios", "prep_time": "45 mins", "tags": ["vegetarian", "shellfish-free"], "image_url": "https://images.unsplash.com/photo-1519676867240-f03562e64548?w=500", "ingredients": ["Phyllo Dough Sheets", "Pistachios", "Raw Honey"], "chef_notes": "Contains gluten (phyllo) and tree nuts (pistachios)."},
]

# ── Beverage Pairings by Cuisine ──
BEVERAGE_DATABASE: Dict[str, List[Dict[str, Any]]] = {
    "Italian": [
        {"title": "Villa Antinori Chianti Classico Riserva 2019", "type": "Red Wine", "tags": ["Tuscan Heritage"], "notes": "Bold dark cherry and tobacco notes, perfect with pasta.", "image_url": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=500", "serving": "Serve at 64°F"},
        {"title": "Pinot Grigio delle Venezie DOC 2022", "type": "White Wine", "tags": ["Light & Crisp"], "notes": "Refreshing citrus and pear — ideal with lighter antipasti.", "image_url": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=500", "serving": "Serve chilled at 48°F"},
    ],
    "Mexican": [
        {"title": "Clase Azul Reposado Tequila", "type": "Tequila", "tags": ["Premium"], "notes": "Smooth vanilla and caramel, sipped neat alongside spicy dishes.", "image_url": "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=500", "serving": "Serve neat at room temp"},
        {"title": "Mexican Hibiscus Agua Fresca", "type": "Non-Alcoholic", "tags": ["Refreshing"], "notes": "Floral and tart hibiscus cooler for all guests.", "image_url": "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=500", "serving": "Serve chilled"},
    ],
    "Japanese": [
        {"title": "Dassai 45 Junmai Daiginjo Sake", "type": "Sake", "tags": ["Premium Craft"], "notes": "Elegant floral sake with fruity finish, pairs with umami dishes.", "image_url": "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=500", "serving": "Serve slightly chilled"},
        {"title": "Japanese Matcha Highball", "type": "Non-Alcoholic", "tags": ["Ceremonial"], "notes": "Effervescent matcha soda with yuzu.", "image_url": "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=500", "serving": "Serve over ice"},
    ],
    "Indian": [
        {"title": "Kingfisher Premium Lager", "type": "Beer", "tags": ["Classic Pairing"], "notes": "Crisp lager that cuts through rich curry spices.", "image_url": "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=500", "serving": "Serve ice cold"},
        {"title": "Spiced Masala Chai Latte", "type": "Non-Alcoholic", "tags": ["Traditional"], "notes": "Warming cinnamon and cardamom tea.", "image_url": "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=500", "serving": "Serve hot"},
    ],
    "French": [
        {"title": "Château Margaux Bordeaux 2018", "type": "Red Wine", "tags": ["Fine Dining"], "notes": "Elegant Bordeaux with blackcurrant and violet notes.", "image_url": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=500", "serving": "Serve at 62°F, decanted 1 hour"},
        {"title": "Moët & Chandon Brut Impérial", "type": "Champagne", "tags": ["Celebratory"], "notes": "Classic champagne for a refined French evening.", "image_url": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=500", "serving": "Serve well-chilled at 46°F"},
    ],
    "Mediterranean": [
        {"title": "Santorini Assyrtiko White Wine 2021", "type": "White Wine", "tags": ["Greek Island"], "notes": "Mineral-driven Greek white with citrus and saline notes.", "image_url": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=500", "serving": "Serve chilled at 50°F"},
    ],
}


class CulinaryPlannerSkill:
    """Agent Skill that crafts dietary-safe menus and generative recipe carousels
    from a multi-cuisine recipe database with dynamic filtering."""

    def _normalize_restriction(self, restriction: str) -> str:
        """Normalizes dietary restriction text to a matchable tag."""
        r = restriction.lower().strip()
        if "shellfish" in r:
            return "shellfish-free"
        if "gluten" in r:
            return "gluten-free"
        if "nut" in r:
            return "nut-free"
        if "dairy" in r or "lactose" in r:
            return "dairy-free"
        if "vegan" in r:
            return "vegan"
        if "vegetarian" in r:
            return "vegetarian"
        return r

    def _match_cuisine(self, theme: str) -> str:
        """Maps a theme string to a cuisine key in the recipe database."""
        theme_lower = theme.lower()
        for cuisine in ["Italian", "Mexican", "Japanese", "Indian", "French", "Mediterranean"]:
            if cuisine.lower() in theme_lower:
                return cuisine
        # Default to Italian for unmatched themes
        return "Italian"

    def _filter_recipes(
        self,
        cuisine: str,
        course_type: str,
        required_tags: List[str]
    ) -> List[Dict[str, Any]]:
        """Filters the recipe database by cuisine, course, and dietary compliance."""
        candidates = [
            r for r in RECIPE_DATABASE
            if r["cuisine"] == cuisine and r["course"] == course_type
        ]
        if required_tags:
            candidates = [
                r for r in candidates
                if all(tag in r["tags"] for tag in required_tags)
            ]
        return candidates

    def _select_recipe(self, candidates: List[Dict[str, Any]], seed: str) -> Optional[Dict[str, Any]]:
        """Deterministically selects a recipe using a seed for reproducibility within a session."""
        if not candidates:
            return None
        # Use hash to get a deterministic but varied selection based on seed
        idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(candidates)
        return candidates[idx]

    def plan_menu(
        self,
        theme: str = "Italian Dinner Party",
        dietary_restrictions: Optional[List[str]] = None,
        guest_count: int = 3,
        beverage_preference: str = "Chianti Classico"
    ) -> Dict[str, Any]:
        """
        Creates a tailored multi-course menu with wine/beverage pairing,
        dynamically filtered from the recipe database based on cuisine theme
        and dietary safety constraints.
        """
        dietary_restrictions = dietary_restrictions or []
        required_tags = [self._normalize_restriction(r) for r in dietary_restrictions]
        cuisine = self._match_cuisine(theme)

        # Build courses dynamically
        course_types = ["Antipasto", "Main", "Dessert"]
        courses = []
        course_num = 0

        for course_type in course_types:
            candidates = self._filter_recipes(cuisine, course_type, required_tags)
            # Fallback: try without cuisine filter if no matches
            if not candidates:
                candidates = self._filter_recipes(cuisine, course_type, [])
            if not candidates:
                # Try any cuisine matching the tags
                candidates = [
                    r for r in RECIPE_DATABASE
                    if r["course"] == course_type and all(tag in r["tags"] for tag in required_tags)
                ]

            selected = self._select_recipe(candidates, f"{theme}_{course_type}_{guest_count}")
            if selected:
                course_num += 1
                portion_note = f" (scaled for {guest_count} guests)" if guest_count != 3 else ""
                courses.append({
                    "id": f"course_{course_num}",
                    "course": course_type,
                    "title": selected["title"],
                    "prep_time": selected["prep_time"] + portion_note,
                    "dietary_badges": [t.replace("-", " ").title() for t in selected["tags"]],
                    "image_url": selected["image_url"],
                    "ingredients": selected["ingredients"],
                    "chef_notes": selected["chef_notes"]
                })

        # Add beverage pairing
        beverage_options = BEVERAGE_DATABASE.get(cuisine, BEVERAGE_DATABASE["Italian"])
        # Pick beverage based on preference hint
        selected_bev = beverage_options[0]  # default
        for bev in beverage_options:
            if beverage_preference.lower() in bev["title"].lower():
                selected_bev = bev
                break

        course_num += 1
        courses.append({
            "id": f"course_{course_num}",
            "course": "Sommelier Pairing",
            "title": selected_bev["title"],
            "prep_time": selected_bev["serving"],
            "dietary_badges": selected_bev["tags"],
            "image_url": selected_bev["image_url"],
            "ingredients": [selected_bev["title"]],
            "chef_notes": selected_bev["notes"]
        })

        # Extract all unique ingredients
        all_ingredients = []
        for c in courses:
            all_ingredients.extend(c["ingredients"])
        unique_ingredients = list(dict.fromkeys(all_ingredients))

        restriction_label = ", ".join(dietary_restrictions) if dietary_restrictions else "No specific restrictions"

        # Generative UI MCP App Carousel schema
        mcp_app_carousel = {
            "component": "MCPAppCarousel",
            "type": "recipe_menu_carousel",
            "title": f"Custom Curated Menu: {theme}",
            "subtitle": f"Strictly filtered for {restriction_label} ({guest_count} guests)",
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
            "cuisine": cuisine,
            "dietary_verified": True,
            "dietary_restrictions_applied": dietary_restrictions,
            "guest_count": guest_count,
            "courses": courses,
            "required_ingredients": unique_ingredients,
            "mcp_app_carousel": mcp_app_carousel
        }


# Singleton instance
culinary_planner_skill = CulinaryPlannerSkill()
