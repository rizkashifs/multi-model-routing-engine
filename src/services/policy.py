from src.core.models import ModelProfile, RoutingRequest

# Policies define which models are blocked and any hard cost caps.
POLICIES: dict[str, dict] = {
    "balanced": {
        "blocked_models": [],
    },
    "cost_sensitive": {
        "blocked_models": ["gpt-4o"],
        "max_cost_override": 0.001,
    },
    "enterprise_only": {
        "blocked_models": [],
        "require_tier": "enterprise",
    },
}


def filter_candidates(
    models: list[ModelProfile],
    request: RoutingRequest,
    policy_name: str = "balanced",
) -> list[ModelProfile]:
    policy = POLICIES.get(policy_name, POLICIES["balanced"])
    blocked = set(policy.get("blocked_models", []))
    max_cost = policy.get("max_cost_override", request.max_cost_per_1k_tokens)

    return [
        m for m in models
        if m.healthy
        and m.model_id not in blocked
        and request.user_tier in m.allowed_tiers
        and request.task_type in m.supported_tasks
        and m.cost_per_1k_tokens <= max_cost
        and m.avg_latency_ms <= request.max_latency_ms
        and m.quality_score >= request.min_quality
    ]
