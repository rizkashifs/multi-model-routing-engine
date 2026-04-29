"""
Run with: python examples/demo.py

Demonstrates routing decisions across different user tiers, task types,
and constraints, including a simulated fallback scenario.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.models import RoutingRequest
from src.services import telemetry
from src.services.router import route_with_fallback

SCENARIOS = [
    {
        "label": "Free user - fast chat",
        "request": RoutingRequest(
            task_type="chat",
            user_tier="free",
            max_latency_ms=1000,
            min_quality=0.7,
            max_cost_per_1k_tokens=0.001,
        ),
    },
    {
        "label": "Pro user - code generation",
        "request": RoutingRequest(
            task_type="code",
            user_tier="pro",
            max_latency_ms=2000,
            min_quality=0.88,
            max_cost_per_1k_tokens=0.01,
        ),
    },
    {
        "label": "Enterprise user - high-quality summarization",
        "request": RoutingRequest(
            task_type="summarization",
            user_tier="enterprise",
            max_latency_ms=3000,
            min_quality=0.85,
            max_cost_per_1k_tokens=0.05,
        ),
    },
    {
        "label": "Pro user - classification with fallback",
        "request": RoutingRequest(
            task_type="classification",
            user_tier="pro",
            max_latency_ms=1500,
            min_quality=0.75,
            max_cost_per_1k_tokens=0.005,
        ),
        "simulate_failure": True,
    },
]


def main():
    print("=== Multi-Model Routing Engine Demo ===\n")

    for scenario in SCENARIOS:
        req = scenario["request"]
        simulate_failure = scenario.get("simulate_failure", False)

        try:
            decision, fallback = route_with_fallback(
                req, simulate_primary_failure=simulate_failure
            )
            telemetry.record(decision, fallback)

            print(f"Scenario: {scenario['label']}")
            print(f"  Selected : {decision.selected_model} (score={decision.score})")
            if fallback:
                print(f"  Fallback : {fallback.original_model} → {fallback.fallback_model}")
                print(f"  Reason   : {fallback.reason}")
            if decision.fallback_models:
                print(f"  Backups  : {', '.join(decision.fallback_models)}")
        except ValueError as e:
            print(f"Scenario: {scenario['label']}")
            print(f"  ERROR: {e}")
        print()

    print("=== Telemetry Summary ===")
    for key, val in telemetry.summary().items():
        print(f"  {key}: {val}")


if __name__ == "__main__":
    main()
