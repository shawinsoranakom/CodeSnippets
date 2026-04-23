def _extract_cost_usd(usage: CompletionUsage | None) -> float | None:
    """Return the provider-reported USD cost on the response usage object.

    OpenRouter attaches a ``cost`` field to the OpenAI-compatible usage object
    when the request body includes ``usage: {"include": True}``.  The typed
    ``CompletionUsage`` does not declare it, so we read it off ``model_extra``
    (pydantic v2's container for extras) to keep access fully typed — no
    ``getattr``.  Mirrors ``backend.copilot.tools.web_search._extract_cost_usd``
    and ``backend.copilot.baseline.service._extract_usage_cost``; keep the
    three in sync.
    """
    if usage is None:
        return None
    extras = usage.model_extra or {}
    if "cost" not in extras:
        return None
    raw = extras["cost"]
    if raw is None:
        logger.error("[simulator] usage.cost is present but null")
        return None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        logger.error("[simulator] usage.cost is not numeric: %r", raw)
        return None
    if not math.isfinite(val) or val < 0:
        logger.error("[simulator] usage.cost is non-finite or negative: %r", val)
        return None
    return val