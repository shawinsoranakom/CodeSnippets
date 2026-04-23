def _extract_cost_usd(usage: CompletionUsage | None) -> float | None:
    """Return the provider-reported USD cost off the response usage.

    OpenRouter piggybacks a ``cost`` field on the OpenAI-compatible
    usage object when the request body includes
    ``usage: {"include": True}``.  The OpenAI SDK's typed
    ``CompletionUsage`` does not declare it, so we read it off
    ``model_extra`` (the pydantic v2 container for extras) to keep
    access fully typed — no ``getattr``.  Mirrors the baseline service
    ``_extract_usage_cost``; keep the two in sync.

    Returns ``None`` when the field is absent, null, non-numeric,
    non-finite, or negative.  Invalid values log at error level because
    they indicate a provider bug worth chasing; plain absences are
    silent so the caller can dedupe the "missing cost" warning.
    """
    if usage is None:
        return None
    extras = usage.model_extra or {}
    if "cost" not in extras:
        return None
    raw = extras["cost"]
    if raw is None:
        logger.error("[web_search] usage.cost is present but null")
        return None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        logger.error("[web_search] usage.cost is not numeric: %r", raw)
        return None
    if not math.isfinite(val) or val < 0:
        logger.error("[web_search] usage.cost is non-finite or negative: %r", val)
        return None
    return val