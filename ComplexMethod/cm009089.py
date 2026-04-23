def _create_usage_metadata(
    oai_token_usage: dict, service_tier: str | None = None
) -> UsageMetadata:
    _input = oai_token_usage.get("prompt_tokens")
    input_tokens = _input if _input is not None else 0
    _output = oai_token_usage.get("completion_tokens")
    output_tokens = _output if _output is not None else 0
    _total = oai_token_usage.get("total_tokens")
    total_tokens = _total if _total is not None else input_tokens + output_tokens
    if service_tier not in {"priority", "flex"}:
        service_tier = None
    service_tier_prefix = f"{service_tier}_" if service_tier else ""
    input_token_details: dict = {
        "audio": (oai_token_usage.get("prompt_tokens_details") or {}).get(
            "audio_tokens"
        ),
        f"{service_tier_prefix}cache_read": (
            oai_token_usage.get("prompt_tokens_details") or {}
        ).get("cached_tokens"),
    }
    output_token_details: dict = {
        "audio": (oai_token_usage.get("completion_tokens_details") or {}).get(
            "audio_tokens"
        ),
        f"{service_tier_prefix}reasoning": (
            oai_token_usage.get("completion_tokens_details") or {}
        ).get("reasoning_tokens"),
    }
    if service_tier is not None:
        # Avoid counting cache and reasoning tokens towards the service tier token
        # counts, since service tier tokens are already priced differently
        input_token_details[service_tier] = input_tokens - input_token_details.get(
            f"{service_tier_prefix}cache_read", 0
        )
        output_token_details[service_tier] = output_tokens - output_token_details.get(
            f"{service_tier_prefix}reasoning", 0
        )
    return UsageMetadata(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        input_token_details=InputTokenDetails(
            **{k: v for k, v in input_token_details.items() if v is not None}
        ),
        output_token_details=OutputTokenDetails(
            **{k: v for k, v in output_token_details.items() if v is not None}
        ),
    )