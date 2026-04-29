from src.core.models import FallbackOutcome, RoutingDecision, RoutingRequest
from src.services.catalog import get_all_models
from src.services.decision import rank_models, score_model
from src.services.policy import filter_candidates


def route(request: RoutingRequest, policy_name: str = "balanced") -> RoutingDecision:
    candidates = filter_candidates(get_all_models(), request, policy_name)

    if not candidates:
        raise ValueError(
            f"No models available for task='{request.task_type}', "
            f"tier='{request.user_tier}', policy='{policy_name}'"
        )

    ranked = rank_models(candidates, request)
    selected = ranked[0]

    return RoutingDecision(
        task_type=request.task_type,
        user_tier=request.user_tier,
        selected_model=selected.model_id,
        score=round(score_model(selected, request), 4),
        fallback_models=[m.model_id for m in ranked[1:]],
        policy_applied=policy_name,
    )


def route_with_fallback(
    request: RoutingRequest,
    policy_name: str = "balanced",
    simulate_primary_failure: bool = False,
) -> tuple[RoutingDecision, FallbackOutcome | None]:
    decision = route(request, policy_name)

    if not simulate_primary_failure:
        return decision, None

    if not decision.fallback_models:
        raise ValueError(
            f"Primary model '{decision.selected_model}' failed and no fallback is available."
        )

    original = decision.selected_model
    fallback_id = decision.fallback_models[0]

    decision.selected_model = fallback_id
    decision.fallback_models = decision.fallback_models[1:]
    decision.used_fallback = True
    decision.fallback_from = original

    outcome = FallbackOutcome(
        original_model=original,
        fallback_model=fallback_id,
        reason="Primary model timeout (simulated)",
    )
    return decision, outcome
