def _create_usage_metadata(token_usage: dict[str, Any]) -> UsageMetadata:
    """Create usage metadata from OpenRouter token usage response.

    OpenRouter may return token counts as floats rather than ints, so all
    values are explicitly cast to int.

    Args:
        token_usage: Token usage dict from the API response.

    Returns:
        Usage metadata with input/output token details.
    """
    _input = token_usage.get("prompt_tokens")
    input_tokens = int(
        _input if _input is not None else (token_usage.get("input_tokens") or 0)
    )
    _output = token_usage.get("completion_tokens")
    output_tokens = int(
        _output if _output is not None else (token_usage.get("output_tokens") or 0)
    )
    _total = token_usage.get("total_tokens")
    total_tokens = int(_total if _total is not None else input_tokens + output_tokens)

    input_details_dict = (
        token_usage.get("prompt_tokens_details")
        or token_usage.get("input_tokens_details")
        or {}
    )
    output_details_dict = (
        token_usage.get("completion_tokens_details")
        or token_usage.get("output_tokens_details")
        or {}
    )

    cache_read = input_details_dict.get("cached_tokens")
    cache_creation = input_details_dict.get("cache_write_tokens")
    input_token_details: dict = {
        "cache_read": int(cache_read) if cache_read is not None else None,
        "cache_creation": int(cache_creation) if cache_creation is not None else None,
    }
    reasoning_tokens = output_details_dict.get("reasoning_tokens")
    output_token_details: dict = {
        "reasoning": int(reasoning_tokens) if reasoning_tokens is not None else None,
    }
    usage_metadata: UsageMetadata = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }

    filtered_input = {k: v for k, v in input_token_details.items() if v is not None}
    if filtered_input:
        usage_metadata["input_token_details"] = InputTokenDetails(**filtered_input)  # type: ignore[typeddict-item]
    filtered_output = {k: v for k, v in output_token_details.items() if v is not None}
    if filtered_output:
        usage_metadata["output_token_details"] = OutputTokenDetails(**filtered_output)  # type: ignore[typeddict-item]
    return usage_metadata