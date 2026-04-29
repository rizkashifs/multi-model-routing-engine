from pydantic import BaseModel


class ModelProfile(BaseModel):
    model_id: str
    provider: str
    cost_per_1k_tokens: float  # USD
    avg_latency_ms: float
    quality_score: float  # 0.0 to 1.0
    supported_tasks: list[str]
    allowed_tiers: list[str]  # "free", "pro", "enterprise"
    healthy: bool = True


class RoutingRequest(BaseModel):
    task_type: str
    user_tier: str = "free"
    max_latency_ms: float = 2000.0
    min_quality: float = 0.7
    max_cost_per_1k_tokens: float = 0.01


class RoutingDecision(BaseModel):
    task_type: str
    user_tier: str
    selected_model: str
    score: float
    fallback_models: list[str]
    policy_applied: str
    used_fallback: bool = False
    fallback_from: str | None = None


class FallbackOutcome(BaseModel):
    original_model: str
    fallback_model: str
    reason: str
