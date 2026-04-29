from src.core.models import ModelProfile

_MODELS: list[ModelProfile] = [
    ModelProfile(
        model_id="gpt-4o",
        provider="openai",
        cost_per_1k_tokens=0.005,
        avg_latency_ms=1200,
        quality_score=0.95,
        supported_tasks=["chat", "code", "summarization", "classification"],
        allowed_tiers=["pro", "enterprise"],
    ),
    ModelProfile(
        model_id="gpt-4o-mini",
        provider="openai",
        cost_per_1k_tokens=0.0002,
        avg_latency_ms=500,
        quality_score=0.80,
        supported_tasks=["chat", "summarization", "classification"],
        allowed_tiers=["free", "pro", "enterprise"],
    ),
    ModelProfile(
        model_id="claude-sonnet-4-6",
        provider="anthropic",
        cost_per_1k_tokens=0.003,
        avg_latency_ms=900,
        quality_score=0.92,
        supported_tasks=["chat", "code", "summarization"],
        allowed_tiers=["pro", "enterprise"],
    ),
    ModelProfile(
        model_id="claude-haiku-4-5",
        provider="anthropic",
        cost_per_1k_tokens=0.0001,
        avg_latency_ms=300,
        quality_score=0.75,
        supported_tasks=["chat", "classification", "summarization"],
        allowed_tiers=["free", "pro", "enterprise"],
    ),
    ModelProfile(
        model_id="llama-3-70b",
        provider="local",
        cost_per_1k_tokens=0.0,
        avg_latency_ms=1500,
        quality_score=0.85,
        supported_tasks=["chat", "code", "summarization"],
        allowed_tiers=["enterprise"],
    ),
    ModelProfile(
        model_id="starcoder2-7b",
        provider="local",
        cost_per_1k_tokens=0.0,
        avg_latency_ms=800,
        quality_score=0.72,
        supported_tasks=["code"],
        allowed_tiers=["free", "pro", "enterprise"],
    ),
]


def get_all_models() -> list[ModelProfile]:
    return list(_MODELS)


def get_model(model_id: str) -> ModelProfile | None:
    return next((m for m in _MODELS if m.model_id == model_id), None)


def set_model_health(model_id: str, healthy: bool) -> None:
    model = get_model(model_id)
    if model:
        model.healthy = healthy
