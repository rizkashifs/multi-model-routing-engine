import pytest

from src.core.models import RoutingRequest
from src.services import telemetry
from src.services.catalog import get_all_models, set_model_health
from src.services.decision import rank_models, score_model
from src.services.policy import filter_candidates
from src.services.router import route, route_with_fallback


@pytest.fixture(autouse=True)
def reset_catalog_health():
    yield
    for m in get_all_models():
        m.healthy = True
    telemetry.clear()


# --- policy filter tests ---

def test_filter_blocks_wrong_tier():
    req = RoutingRequest(task_type="chat", user_tier="free")
    candidates = filter_candidates(get_all_models(), req)
    model_ids = [m.model_id for m in candidates]
    assert "gpt-4o" not in model_ids  # pro/enterprise only
    assert "llama-3-70b" not in model_ids  # enterprise only


def test_filter_blocks_wrong_task():
    req = RoutingRequest(task_type="code", user_tier="free", max_cost_per_1k_tokens=0.01)
    candidates = filter_candidates(get_all_models(), req)
    model_ids = [m.model_id for m in candidates]
    assert "gpt-4o-mini" not in model_ids  # doesn't support code


def test_filter_blocks_unhealthy_model():
    set_model_health("claude-haiku-4-5", False)
    req = RoutingRequest(task_type="chat", user_tier="free")
    candidates = filter_candidates(get_all_models(), req)
    assert all(m.model_id != "claude-haiku-4-5" for m in candidates)


def test_filter_respects_cost_constraint():
    req = RoutingRequest(task_type="chat", user_tier="pro", max_cost_per_1k_tokens=0.0005)
    candidates = filter_candidates(get_all_models(), req)
    assert all(m.cost_per_1k_tokens <= 0.0005 for m in candidates)


def test_filter_respects_quality_constraint():
    req = RoutingRequest(task_type="chat", user_tier="pro", min_quality=0.9)
    candidates = filter_candidates(get_all_models(), req)
    assert all(m.quality_score >= 0.9 for m in candidates)


def test_filter_respects_latency_constraint():
    req = RoutingRequest(task_type="chat", user_tier="pro", max_latency_ms=600)
    candidates = filter_candidates(get_all_models(), req)
    assert all(m.avg_latency_ms <= 600 for m in candidates)


def test_cost_sensitive_policy_blocks_expensive_models():
    req = RoutingRequest(task_type="chat", user_tier="pro")
    candidates = filter_candidates(get_all_models(), req, policy_name="cost_sensitive")
    assert all(m.model_id != "gpt-4o" for m in candidates)


# --- scoring and ranking tests ---

def test_higher_quality_scores_higher_all_else_equal():
    from src.core.models import ModelProfile

    req = RoutingRequest(task_type="chat", user_tier="pro")
    common = dict(provider="test", cost_per_1k_tokens=0.001, avg_latency_ms=500,
                  supported_tasks=["chat"], allowed_tiers=["pro"])
    high_quality = ModelProfile(model_id="high", quality_score=0.95, **common)
    low_quality = ModelProfile(model_id="low", quality_score=0.70, **common)
    assert score_model(high_quality, req) > score_model(low_quality, req)


def test_rank_models_returns_descending_scores():
    req = RoutingRequest(task_type="chat", user_tier="enterprise")
    models = get_all_models()
    ranked = rank_models(models, req)
    scores = [score_model(m, req) for m in ranked]
    assert scores == sorted(scores, reverse=True)


# --- router tests ---

def test_route_returns_valid_decision():
    req = RoutingRequest(task_type="chat", user_tier="pro")
    decision = route(req)
    assert decision.selected_model
    assert 0 < decision.score <= 1


def test_route_free_chat_picks_affordable_model():
    req = RoutingRequest(task_type="chat", user_tier="free", max_cost_per_1k_tokens=0.001)
    decision = route(req)
    model = next(m for m in get_all_models() if m.model_id == decision.selected_model)
    assert model.cost_per_1k_tokens <= 0.001
    assert "free" in model.allowed_tiers


def test_route_raises_when_no_candidates():
    req = RoutingRequest(task_type="chat", user_tier="free", min_quality=0.99)
    with pytest.raises(ValueError, match="No models available"):
        route(req)


def test_route_with_fallback_no_failure():
    req = RoutingRequest(task_type="chat", user_tier="pro")
    decision, fallback = route_with_fallback(req)
    assert fallback is None
    assert not decision.used_fallback


def test_route_with_fallback_uses_next_best():
    req = RoutingRequest(task_type="chat", user_tier="pro")
    decision_normal = route(req)
    primary = decision_normal.selected_model

    decision, fallback = route_with_fallback(req, simulate_primary_failure=True)
    assert fallback is not None
    assert fallback.original_model == primary
    assert decision.selected_model != primary
    assert decision.used_fallback is True
    assert decision.fallback_from == primary


def test_route_with_fallback_raises_when_only_one_candidate():
    # Only starcoder2-7b supports code for free tier with low quality threshold
    req = RoutingRequest(
        task_type="code",
        user_tier="free",
        min_quality=0.0,
        max_cost_per_1k_tokens=0.001,
        max_latency_ms=5000,
    )
    # Mark all other code models unhealthy or expensive so only one remains
    set_model_health("gpt-4o", False)
    set_model_health("claude-sonnet-4-6", False)
    set_model_health("llama-3-70b", False)

    with pytest.raises(ValueError, match="no fallback"):
        route_with_fallback(req, simulate_primary_failure=True)


# --- telemetry tests ---

def test_telemetry_records_decision():
    req = RoutingRequest(task_type="chat", user_tier="pro")
    decision = route(req)
    telemetry.record(decision)
    log = telemetry.get_log()
    assert len(log) == 1
    assert log[0]["selected_model"] == decision.selected_model


def test_telemetry_summary():
    req = RoutingRequest(task_type="chat", user_tier="pro")
    decision = route(req)
    telemetry.record(decision)
    s = telemetry.summary()
    assert s["total_requests"] == 1
    assert s["fallback_rate"] == 0.0
