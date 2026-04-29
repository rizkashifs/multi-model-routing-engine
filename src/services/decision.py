from src.core.models import ModelProfile, RoutingRequest


def score_model(model: ModelProfile, request: RoutingRequest) -> float:
    """Score a model 0-1. Higher is better. Quality weighted most heavily."""
    # Normalize cost: 0 cost → score 1.0, at max_cost → score 0.0
    max_cost = request.max_cost_per_1k_tokens or 0.01
    cost_score = 1.0 - min(model.cost_per_1k_tokens / max_cost, 1.0)

    # Normalize latency: 0ms → score 1.0, at max_latency → score 0.0
    latency_score = 1.0 - min(model.avg_latency_ms / request.max_latency_ms, 1.0)

    return 0.5 * model.quality_score + 0.3 * latency_score + 0.2 * cost_score


def rank_models(models: list[ModelProfile], request: RoutingRequest) -> list[ModelProfile]:
    return sorted(models, key=lambda m: score_model(m, request), reverse=True)
