from fastapi import FastAPI, HTTPException, Query

from src.core.models import RoutingDecision, RoutingRequest
from src.services import telemetry
from src.services.router import route

app = FastAPI(
    title="Multi-Model Routing Engine",
    description="Routes requests to the best model based on cost, latency, and quality.",
)


@app.post("/route", response_model=RoutingDecision)
def route_request(
    request: RoutingRequest,
    policy: str = Query(default="balanced", description="Policy name to apply"),
):
    try:
        decision = route(request, policy_name=policy)
        telemetry.record(decision)
        return decision
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/telemetry/summary")
def get_summary():
    return telemetry.summary()


@app.get("/telemetry/log")
def get_log():
    return telemetry.get_log()


@app.get("/health")
def health():
    return {"status": "ok"}
