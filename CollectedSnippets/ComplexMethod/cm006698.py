def extract_usage_from_message(message: Any) -> Usage | None:
    """Extract token usage from an AIMessage's metadata.

    Tries three strategies in priority order:
    1. usage_metadata (LangChain standard, works for Ollama and newer providers)
    2. response_metadata["token_usage"] (OpenAI format)
    3. response_metadata["usage"] (Anthropic format)

    Args:
        message: An AIMessage or similar object with usage_metadata/response_metadata.

    Returns:
        Usage with token counts, or None if no usage data is available.
    """
    # Strategy 1: usage_metadata (LangChain standard)
    usage_metadata = getattr(message, "usage_metadata", None)
    if usage_metadata and isinstance(usage_metadata, dict):
        input_tokens = usage_metadata.get("input_tokens", 0) or 0
        output_tokens = usage_metadata.get("output_tokens", 0) or 0
        if input_tokens or output_tokens:
            return Usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            )

    response_metadata = getattr(message, "response_metadata", None)
    if not response_metadata:
        return None

    # Strategy 2: response_metadata["token_usage"] (OpenAI format)
    if "token_usage" in response_metadata:
        token_usage = response_metadata["token_usage"]
        return Usage(
            input_tokens=token_usage.get("prompt_tokens"),
            output_tokens=token_usage.get("completion_tokens"),
            total_tokens=token_usage.get("total_tokens"),
        )

    # Strategy 3: response_metadata["usage"] (Anthropic format)
    if "usage" in response_metadata:
        usage = response_metadata["usage"]
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        return Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=(input_tokens or 0) + (output_tokens or 0) if input_tokens or output_tokens else None,
        )

    return None