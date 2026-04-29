# Architecture Decisions

## ADR-001: Routing is policy-driven

Model choice should be controlled by explicit policies rather than scattered conditional logic.

## ADR-002: Fallbacks are first-class behavior

Routing architecture must represent degradation paths when models are unavailable, slow, expensive, or failing quality checks.
