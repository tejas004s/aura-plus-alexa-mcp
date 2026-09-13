"""
sustainability.py - Green AI & Carbon Footprint Tracking Module

Tracks resource consumption, estimates environmental impact of LLM inference
and tool execution, and provides optimization recommendations.
Inspired by GitLab AI Hackathon Green Agent category winners.
"""

import time
from typing import Dict, Any, List
from dataclasses import dataclass, field


# ─── Energy Constants ───────────────────────────────────────────────────────
# ~0.0003 kWh per 1000 tokens (based on Anthropic Claude estimates)
KWH_PER_TOKEN = 0.0000003
# US grid average: ~0.4 kg CO2 per kWh (EPA 2024)
CO2_KG_PER_KWH = {
    "us-east-1": 0.379,      # Virginia (mixed grid)
    "us-west-2": 0.098,      # Oregon (heavy hydro — greenest)
    "eu-west-1": 0.296,      # Ireland (wind + gas)
    "ap-northeast-1": 0.462, # Tokyo (coal heavy)
    "default": 0.400
}


@dataclass
class ToolInvocation:
    """Records a single tool execution for tracking."""
    tool_name: str
    input_tokens: int
    output_tokens: int
    execution_time_ms: float
    timestamp: float = field(default_factory=time.time)


class ResourceTracker:
    """Tracks compute resources, estimates carbon footprint, and suggests optimizations."""

    def __init__(self):
        self._invocations: List[ToolInvocation] = []
        self._session_start = time.time()

    def track_request(
        self,
        tool_name: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        execution_time_ms: float = 0.0
    ) -> None:
        """Records a tool invocation for resource tracking."""
        self._invocations.append(ToolInvocation(
            tool_name=tool_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            execution_time_ms=execution_time_ms
        ))

    def get_session_metrics(self) -> Dict[str, Any]:
        """Returns aggregated resource metrics for the current session."""
        total_input = sum(inv.input_tokens for inv in self._invocations)
        total_output = sum(inv.output_tokens for inv in self._invocations)
        total_tokens = total_input + total_output
        total_exec_ms = sum(inv.execution_time_ms for inv in self._invocations)
        uptime_s = round(time.time() - self._session_start, 1)

        kwh = self.estimate_energy_kwh(total_tokens)
        co2 = self.estimate_carbon_footprint_grams(total_tokens)

        return {
            "session_uptime_seconds": uptime_s,
            "total_requests": len(self._invocations),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_tokens,
            "total_execution_time_ms": round(total_exec_ms, 1),
            "estimated_energy_kwh": round(kwh, 8),
            "estimated_co2_grams": round(co2, 4),
            "tools_invoked": list(set(inv.tool_name for inv in self._invocations)),
            "green_score": self._calculate_green_score(total_tokens, len(self._invocations))
        }

    def estimate_energy_kwh(self, total_tokens: int) -> float:
        """Estimates energy consumption in kWh based on token count."""
        return total_tokens * KWH_PER_TOKEN

    def estimate_carbon_footprint_grams(
        self,
        total_tokens: int,
        region: str = "us-east-1"
    ) -> float:
        """Estimates CO2 emissions in grams based on token usage and cloud region."""
        kwh = self.estimate_energy_kwh(total_tokens)
        co2_per_kwh = CO2_KG_PER_KWH.get(region, CO2_KG_PER_KWH["default"])
        return kwh * co2_per_kwh * 1000  # Convert kg to grams

    def _calculate_green_score(self, total_tokens: int, request_count: int) -> str:
        """Assigns a sustainability grade based on token efficiency."""
        if request_count == 0:
            return "A+ (No compute used)"
        avg_tokens = total_tokens / request_count
        if avg_tokens < 500:
            return "A+ (Highly Efficient)"
        elif avg_tokens < 1500:
            return "A (Efficient)"
        elif avg_tokens < 3000:
            return "B (Moderate)"
        elif avg_tokens < 5000:
            return "C (Consider Optimization)"
        else:
            return "D (High Consumption — Optimize Prompts)"

    def get_efficiency_report(self) -> Dict[str, Any]:
        """Returns optimization suggestions based on usage patterns."""
        metrics = self.get_session_metrics()
        suggestions = []

        if metrics["total_tokens"] > 5000:
            suggestions.append("Consider caching frequent memory lookups to reduce redundant LLM calls.")
        if metrics["total_requests"] > 8:
            suggestions.append("Batch related tool calls into parallel execution groups to reduce round-trips.")
        if metrics["estimated_co2_grams"] > 0.5:
            suggestions.append(f"Deploy to us-west-2 (Oregon) to reduce CO2 by ~74% via hydroelectric grid.")

        if not suggestions:
            suggestions.append("Current usage is within efficient parameters. No optimization needed.")

        return {
            "metrics": metrics,
            "optimization_suggestions": suggestions,
            "recommended_region": "us-west-2 (Oregon — lowest carbon grid)",
            "carbon_offset_equivalent": f"~{max(1, int(metrics['estimated_co2_grams'] * 100))} meters of car travel avoided"
        }

    def reset(self) -> None:
        """Resets session tracking."""
        self._invocations.clear()
        self._session_start = time.time()


# Singleton instance
resource_tracker = ResourceTracker()
