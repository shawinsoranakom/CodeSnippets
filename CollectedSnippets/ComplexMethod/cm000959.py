def _make_usage_chunk(
    *,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost: float | str | None | object = _COST_MISSING,
    cached_tokens: int | None = None,
    cache_creation_input_tokens: int | None = None,
):
    """Build a mock streaming chunk carrying usage (and optionally cost).

    Provider-specific fields (``cost`` on usage, ``cache_creation_input_tokens``
    on prompt_tokens_details) are set on ``model_extra`` because that's where
    the baseline helper reads them from (typed ``CompletionUsage.model_extra``
    rather than ``getattr``). Pass ``cost=None`` to emit an explicit-null cost
    key; omit ``cost`` entirely to leave the key absent.
    """
    chunk = MagicMock()
    chunk.choices = []
    chunk.usage = MagicMock()
    chunk.usage.prompt_tokens = prompt_tokens
    chunk.usage.completion_tokens = completion_tokens
    usage_extras: dict[str, float | str | None] = {}
    if cost is not _COST_MISSING:
        usage_extras["cost"] = cost  # type: ignore[assignment]
    chunk.usage.model_extra = usage_extras

    if cached_tokens is not None or cache_creation_input_tokens is not None:
        # Build a real ``PromptTokensDetails`` so ``getattr(ptd,
        # "cache_write_tokens", None)`` returns ``None`` on this SDK version
        # (rather than a truthy MagicMock attribute) and the extraction
        # helper's typed-attr vs model_extra fallback resolves correctly.
        from openai.types.completion_usage import PromptTokensDetails

        ptd = PromptTokensDetails.model_validate({"cached_tokens": cached_tokens or 0})
        if cache_creation_input_tokens is not None:
            if ptd.model_extra is None:
                object.__setattr__(ptd, "__pydantic_extra__", {})
            assert ptd.model_extra is not None
            ptd.model_extra["cache_creation_input_tokens"] = cache_creation_input_tokens
        chunk.usage.prompt_tokens_details = ptd
    else:
        chunk.usage.prompt_tokens_details = None

    return chunk