from datetime import datetime, timezone

from src.core.models import FallbackOutcome, RoutingDecision

_log: list[dict] = []


def record(decision: RoutingDecision, fallback: FallbackOutcome | None = None) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_type": decision.task_type,
        "user_tier": decision.user_tier,
        "selected_model": decision.selected_model,
        "score": decision.score,
        "policy": decision.policy_applied,
        "used_fallback": decision.used_fallback,
    }
    if fallback:
        entry["fallback_from"] = fallback.original_model
        entry["fallback_reason"] = fallback.reason
    _log.append(entry)


def get_log() -> list[dict]:
    return list(_log)


def summary() -> dict:
    if not _log:
        return {"total_requests": 0}

    models_used = [e["selected_model"] for e in _log]
    fallback_count = sum(1 for e in _log if e["used_fallback"])

    return {
        "total_requests": len(_log),
        "fallback_rate": round(fallback_count / len(_log), 3),
        "models_used": {m: models_used.count(m) for m in set(models_used)},
    }


def clear() -> None:
    _log.clear()
