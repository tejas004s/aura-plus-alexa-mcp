"""
calendar_concierge.py - Agent Skill for Alexa+ Smart Calendar & Schedule Orchestration

Coordinates events, detects scheduling conflicts using time-range overlap analysis,
reserves preparation buffers, and manages invitations across family calendars.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


# ─── Day/Time Parsing Utilities ─────────────────────────────────────────────
DAY_ORDER = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
             "friday": 4, "saturday": 5, "sunday": 6}


def parse_event_time(time_str: str) -> Optional[tuple]:
    """Parses 'Friday 7:00 PM' into (day_index, minutes_from_midnight) for comparison."""
    parts = time_str.strip().split(" ", 1)
    if len(parts) < 2:
        return None
    day_name = parts[0].lower().rstrip(",")
    time_part = parts[1].strip()
    day_idx = DAY_ORDER.get(day_name)
    if day_idx is None:
        return None
    try:
        # Parse "7:00 PM" or "2:30 PM"
        dt = datetime.strptime(time_part.upper(), "%I:%M %p")
        minutes = dt.hour * 60 + dt.minute
        return (day_idx, minutes)
    except ValueError:
        try:
            dt = datetime.strptime(time_part.upper(), "%I %p")
            minutes = dt.hour * 60 + dt.minute
            return (day_idx, minutes)
        except ValueError:
            return None


def times_overlap(start_a, end_a, start_b, end_b) -> bool:
    """Checks if two time ranges (day_idx, minutes) overlap."""
    if start_a is None or end_a is None or start_b is None or end_b is None:
        return False
    # Convert to absolute minutes (day * 1440 + minutes)
    abs_start_a = start_a[0] * 1440 + start_a[1]
    abs_end_a = end_a[0] * 1440 + end_a[1]
    abs_start_b = start_b[0] * 1440 + start_b[1]
    abs_end_b = end_b[0] * 1440 + end_b[1]
    return abs_start_a < abs_end_b and abs_start_b < abs_end_a


class CalendarConciergeSkill:
    """Agent Skill managing calendar events, conflict detection, reminders, and family schedules."""

    def __init__(self):
        self._events: List[Dict[str, Any]] = [
            {
                "id": "evt_existing_01",
                "title": "Work Focus Time",
                "start": "Friday 2:00 PM",
                "end": "Friday 4:30 PM",
                "status": "confirmed"
            }
        ]

    def _detect_conflicts(self, start_time: str, end_time: str, exclude_id: str = "") -> List[Dict[str, Any]]:
        """Finds all existing events that overlap with the proposed time range."""
        new_start = parse_event_time(start_time)
        new_end = parse_event_time(end_time)
        conflicts = []
        for evt in self._events:
            if evt.get("id") == exclude_id:
                continue
            evt_start = parse_event_time(evt["start"])
            evt_end = parse_event_time(evt["end"])
            if times_overlap(new_start, new_end, evt_start, evt_end):
                conflicts.append(evt)
        return conflicts

    def _suggest_alternatives(self, start_time: str, end_time: str) -> List[str]:
        """Suggests alternative time slots when a conflict is detected."""
        new_start = parse_event_time(start_time)
        new_end = parse_event_time(end_time)
        if not new_start or not new_end:
            return []
        duration_mins = (new_end[0] * 1440 + new_end[1]) - (new_start[0] * 1440 + new_start[1])
        day_idx = new_start[0]
        day_name = [k for k, v in DAY_ORDER.items() if v == day_idx][0].capitalize()

        alternatives = []
        # Try 1 hour later
        later_start_mins = new_start[1] + 60
        if later_start_mins + duration_mins <= 23 * 60:
            alt_start_h = later_start_mins // 60
            alt_start_m = later_start_mins % 60
            alt_end_mins = later_start_mins + duration_mins
            alt_end_h = alt_end_mins // 60
            alt_end_m = alt_end_mins % 60
            period_s = "PM" if alt_start_h >= 12 else "AM"
            period_e = "PM" if alt_end_h >= 12 else "AM"
            h_s = alt_start_h if alt_start_h <= 12 else alt_start_h - 12
            h_e = alt_end_h if alt_end_h <= 12 else alt_end_h - 12
            if h_s == 0: h_s = 12
            if h_e == 0: h_e = 12
            alternatives.append(f"{day_name} {h_s}:{alt_start_m:02d} {period_s} - {h_e}:{alt_end_m:02d} {period_e}")

        # Try next day
        next_day_idx = (day_idx + 1) % 7
        next_day_name = [k for k, v in DAY_ORDER.items() if v == next_day_idx][0].capitalize()
        h_s = new_start[1] // 60
        m_s = new_start[1] % 60
        period_s = "PM" if h_s >= 12 else "AM"
        h_s_12 = h_s if h_s <= 12 else h_s - 12
        if h_s_12 == 0: h_s_12 = 12
        alternatives.append(f"{next_day_name} {h_s_12}:{m_s:02d} {period_s} (same time, next day)")

        return alternatives

    def schedule_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        attendees: Optional[List[str]] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Schedules a new event with real conflict detection and automatic reminders.
        """
        attendees = attendees or ["Alex Henderson"]
        conflicts = self._detect_conflicts(start_time, end_time)

        event_obj = {
            "id": f"evt_{len(self._events) + 1}",
            "title": title,
            "start": start_time,
            "end": end_time,
            "attendees": attendees,
            "notes": notes,
            "status": "confirmed" if not conflicts else "confirmed_with_overlap",
            "calendar": "Family & Social Calendar",
            "reminders": ["1 day before", "2 hours before"]
        }
        self._events.append(event_obj)

        conflict_info = {}
        if conflicts:
            conflict_info = {
                "conflicting_events": [
                    {"id": c["id"], "title": c["title"], "start": c["start"], "end": c["end"]}
                    for c in conflicts
                ],
                "suggested_alternatives": self._suggest_alternatives(start_time, end_time)
            }

        mcp_app_card = {
            "component": "MCPAppCard",
            "type": "calendar_event_confirmation",
            "title": f"Calendar Updated: {title}" + (" ⚠️ Overlap" if conflicts else ""),
            "subtitle": f"{start_time} - {end_time}",
            "data": event_obj,
            "actions": [
                {
                    "id": "send_invites",
                    "label": f"Send Invites ({len(attendees)} people)",
                    "style": "primary",
                    "payload": {"event_id": event_obj["id"], "action": "send_notifications"}
                }
            ]
        }

        return {
            "event": event_obj,
            "conflict_detected": len(conflicts) > 0,
            **conflict_info,
            "mcp_app_card": mcp_app_card
        }

    def delete_event(self, event_id: str) -> Dict[str, Any]:
        """Removes an event from the calendar by ID."""
        for i, evt in enumerate(self._events):
            if evt["id"] == event_id:
                removed = self._events.pop(i)
                return {"success": True, "deleted_event": removed}
        return {"success": False, "error": f"Event '{event_id}' not found."}

    def get_events_for_day(self, day: str) -> Dict[str, Any]:
        """Returns all events scheduled for a specific day name."""
        day_lower = day.lower().strip()
        matching = [
            evt for evt in self._events
            if evt["start"].lower().startswith(day_lower)
        ]
        return {
            "day": day,
            "event_count": len(matching),
            "events": matching
        }

    def list_upcoming_events(self) -> List[Dict[str, Any]]:
        return self._events


# Singleton instance
calendar_concierge_skill = CalendarConciergeSkill()
