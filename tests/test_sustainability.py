"""
test_sustainability.py - Tests for Green AI & Carbon Footprint Tracking
"""

import pytest
from aws_orchestrator.sustainability import ResourceTracker, resource_tracker


def test_resource_tracker_init():
    tracker = ResourceTracker()
    metrics = tracker.get_session_metrics()
    assert metrics["total_requests"] == 0
    assert metrics["total_tokens"] == 0
    assert metrics["estimated_co2_grams"] == 0.0


def test_track_single_request():
    tracker = ResourceTracker()
    tracker.track_request("test_tool", input_tokens=100, output_tokens=50, execution_time_ms=250)
    metrics = tracker.get_session_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["total_input_tokens"] == 100
    assert metrics["total_output_tokens"] == 50
    assert metrics["total_tokens"] == 150


def test_track_multiple_requests():
    tracker = ResourceTracker()
    tracker.track_request("tool_a", input_tokens=200, output_tokens=100)
    tracker.track_request("tool_b", input_tokens=300, output_tokens=200)
    metrics = tracker.get_session_metrics()
    assert metrics["total_requests"] == 2
    assert metrics["total_tokens"] == 800
    assert "tool_a" in metrics["tools_invoked"]
    assert "tool_b" in metrics["tools_invoked"]


def test_carbon_footprint_estimation():
    tracker = ResourceTracker()
    co2 = tracker.estimate_carbon_footprint_grams(10000, region="us-east-1")
    assert co2 > 0
    # Oregon should produce less CO2 than Virginia
    co2_oregon = tracker.estimate_carbon_footprint_grams(10000, region="us-west-2")
    assert co2_oregon < co2


def test_energy_estimation():
    tracker = ResourceTracker()
    kwh = tracker.estimate_energy_kwh(1000)
    assert kwh == pytest.approx(0.0003, abs=0.0001)


def test_green_score_efficient():
    tracker = ResourceTracker()
    tracker.track_request("small_tool", input_tokens=100, output_tokens=50)
    metrics = tracker.get_session_metrics()
    assert "A+" in metrics["green_score"]


def test_green_score_moderate():
    tracker = ResourceTracker()
    for _ in range(3):
        tracker.track_request("big_tool", input_tokens=1000, output_tokens=500)
    metrics = tracker.get_session_metrics()
    assert "A+" not in metrics["green_score"]  # Not efficient at 1500 avg tokens


def test_efficiency_report():
    tracker = ResourceTracker()
    for _ in range(10):
        tracker.track_request("heavy_tool", input_tokens=500, output_tokens=300)
    report = tracker.get_efficiency_report()
    assert "optimization_suggestions" in report
    assert len(report["optimization_suggestions"]) > 0
    assert "recommended_region" in report


def test_reset():
    tracker = ResourceTracker()
    tracker.track_request("tool", input_tokens=100, output_tokens=50)
    tracker.reset()
    metrics = tracker.get_session_metrics()
    assert metrics["total_requests"] == 0


def test_singleton_instance():
    assert resource_tracker is not None
    assert isinstance(resource_tracker, ResourceTracker)
