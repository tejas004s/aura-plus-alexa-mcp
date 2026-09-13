"""
household_memory.py - Agent Skill for Alexa+ Cross-Session Household Memory

Maintains persistent long-term knowledge of family members, dietary restrictions,
allergies, room preferences, and connected home configurations across interactions.
"""

from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path

PROFILE_PATH = Path(__file__).resolve().parent.parent / "data" / "household_profile.json"


class HouseholdMemorySkill:
    """Agent Skill managing long-term household context and personal preferences."""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or PROFILE_PATH
        self._memory = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.data_path.exists():
            return {
                "household_id": "default",
                "name": "My Home",
                "members": [],
                "preferences": {},
                "connected_devices": []
            }
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self) -> None:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self._memory, f, indent=2)

    def get_household_summary(self) -> Dict[str, Any]:
        """Returns the full household profile, active members, and preferences."""
        return self._memory

    def query_member_dietary(self, member_name_or_relation: str) -> Dict[str, Any]:
        """
        Retrieves dietary restrictions and culinary preferences for a specific member
        (e.g., 'Mom', 'Elena', 'Dad', 'Robert').
        """
        query_lower = member_name_or_relation.lower()
        matched = []
        for m in self._memory.get("members", []):
            if query_lower in m["name"].lower() or query_lower in m["relation"].lower():
                matched.append(m)

        if not matched:
            return {
                "found": False,
                "message": f"No specific profile found matching '{member_name_or_relation}'.",
                "all_members": [m["name"] for m in self._memory.get("members", [])]
            }

        return {
            "found": True,
            "profiles": matched,
            "dietary_restrictions": [d for m in matched for d in m.get("dietary_restrictions", [])],
            "preferences": [p for m in matched for p in m.get("preferences", [])]
        }

    def get_all_dietary_restrictions(self) -> Dict[str, List[str]]:
        """Returns combined dietary safety constraints across all active household members."""
        restrictions = {}
        for m in self._memory.get("members", []):
            if m.get("dietary_restrictions"):
                restrictions[m["name"]] = m["dietary_restrictions"]
        return {
            "household_dietary_rules": restrictions,
            "critical_allergies": [
                f"{m['name']}: {r}"
                for m in self._memory.get("members", [])
                for r in m.get("dietary_restrictions", [])
                if "allergy" in r.lower() or "strict" in r.lower()
            ]
        }

    def remember_preference(self, member_name: str, preference_or_fact: str, category: str = "preference") -> Dict[str, Any]:
        """
        Persists a newly learned preference or fact about a member across sessions.
        """
        found = False
        for m in self._memory.get("members", []):
            if member_name.lower() in m["name"].lower():
                found = True
                if category == "allergy" or "allerg" in preference_or_fact.lower():
                    if preference_or_fact not in m.setdefault("dietary_restrictions", []):
                        m["dietary_restrictions"].append(preference_or_fact)
                else:
                    if preference_or_fact not in m.setdefault("preferences", []):
                        m["preferences"].append(preference_or_fact)
                break

        if not found:
            # Create member
            self._memory.setdefault("members", []).append({
                "name": member_name,
                "relation": "Guest",
                "dietary_restrictions": [preference_or_fact] if "allerg" in preference_or_fact.lower() else [],
                "preferences": [preference_or_fact] if "allerg" not in preference_or_fact.lower() else [],
                "frequent_guest": False
            })

        self._save()
        return {
            "success": True,
            "message": f"Successfully committed '{preference_or_fact}' to memory for {member_name}.",
            "member": member_name
        }


# Singleton instance
household_memory_skill = HouseholdMemorySkill()
