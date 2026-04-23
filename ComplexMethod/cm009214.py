def _create_usage_metadata(anthropic_usage: BaseModel) -> UsageMetadata:
    """Create LangChain `UsageMetadata` from Anthropic `Usage` data.

    Note:
        Anthropic's `input_tokens` excludes cached tokens, so we manually add
        `cache_read` and `cache_creation` tokens to get the true total.
    """
    input_token_details: dict = {
        "cache_read": getattr(anthropic_usage, "cache_read_input_tokens", None),
        "cache_creation": getattr(anthropic_usage, "cache_creation_input_tokens", None),
    }

    # Add cache TTL information if provided (5-minute and 1-hour ephemeral cache)
    cache_creation = getattr(anthropic_usage, "cache_creation", None)

    # Currently just copying over the 5m and 1h keys, but if more are added in the
    # future we'll need to expand this tuple
    cache_creation_keys = ("ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens")
    specific_cache_creation_tokens = 0
    if cache_creation:
        if isinstance(cache_creation, BaseModel):
            cache_creation = cache_creation.model_dump()
        for k in cache_creation_keys:
            specific_cache_creation_tokens += cache_creation.get(k, 0)
            input_token_details[k] = cache_creation.get(k)
        if not isinstance(specific_cache_creation_tokens, int):
            specific_cache_creation_tokens = 0
        if specific_cache_creation_tokens > 0:
            # Remove generic key to avoid double counting cache creation tokens
            input_token_details["cache_creation"] = 0

    # Calculate total input tokens: Anthropic's `input_tokens` excludes cached tokens,
    # so we need to add them back to get the true total input token count
    input_tokens = (
        (getattr(anthropic_usage, "input_tokens", 0) or 0)  # Base input tokens
        + (input_token_details["cache_read"] or 0)  # Tokens read from cache
        + (
            specific_cache_creation_tokens or input_token_details["cache_creation"] or 0
        )  # Tokens used to create cache
    )
    output_tokens = getattr(anthropic_usage, "output_tokens", 0) or 0

    return UsageMetadata(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        input_token_details=InputTokenDetails(
            **{k: v for k, v in input_token_details.items() if v is not None},
        ),
    )