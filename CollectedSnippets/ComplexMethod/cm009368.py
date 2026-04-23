def _create_usage_metadata(groq_token_usage: dict) -> UsageMetadata:
    """Create usage metadata from Groq token usage response.

    Args:
        groq_token_usage: Token usage dict from Groq API response.

    Returns:
        Usage metadata dict with input/output token details.
    """
    # Support both formats: new Responses API uses "input_tokens",
    # Chat Completions API uses "prompt_tokens"
    _input = groq_token_usage.get("input_tokens")
    input_tokens = (
        _input if _input is not None else (groq_token_usage.get("prompt_tokens") or 0)
    )
    _output = groq_token_usage.get("output_tokens")
    output_tokens = (
        _output
        if _output is not None
        else (groq_token_usage.get("completion_tokens") or 0)
    )
    _total = groq_token_usage.get("total_tokens")
    total_tokens = _total if _total is not None else input_tokens + output_tokens

    # Support both formats for token details:
    # Responses API uses "*_tokens_details", Chat Completions API might use
    # "prompt_token_details"
    input_details_dict = (
        groq_token_usage.get("input_tokens_details")
        or groq_token_usage.get("prompt_tokens_details")
        or {}
    )
    output_details_dict = (
        groq_token_usage.get("output_tokens_details")
        or groq_token_usage.get("completion_tokens_details")
        or {}
    )

    input_token_details: dict = {
        "cache_read": input_details_dict.get("cached_tokens"),
    }
    output_token_details: dict = {
        "reasoning": output_details_dict.get("reasoning_tokens"),
    }
    usage_metadata: UsageMetadata = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }

    if filtered_input := {k: v for k, v in input_token_details.items() if v}:
        usage_metadata["input_token_details"] = InputTokenDetails(**filtered_input)  # type: ignore[typeddict-item]
    if filtered_output := {k: v for k, v in output_token_details.items() if v}:
        usage_metadata["output_token_details"] = OutputTokenDetails(**filtered_output)  # type: ignore[typeddict-item]
    return usage_metadata