def extract_usage_from_llm_result(response: Any) -> Usage | None:
    """Extract token usage from an LLMResult object.

    Consolidates the extraction logic used by both the token usage tracking feature
    (TokenUsageCallbackHandler) and the traces feature (NativeCallbackHandler) into
    a single source of truth.

    Tries four strategies in priority order:
    1. llm_output["token_usage"] (legacy OpenAI path, LLMResult-specific)
    2. generations[].message via extract_usage_from_message() (usage_metadata, response_metadata)
    3. generations[].generation_info["token_usage"] or ["usage"] (older Anthropic adapters)

    Args:
        response: An LLMResult or similar object with llm_output and generations attributes.

    Returns:
        Usage with token counts, or None if no usage data is available.
    """
    # Strategy 1: llm_output["token_usage"] (legacy OpenAI, only on LLMResult)
    llm_output = getattr(response, "llm_output", None) or {}
    if isinstance(llm_output, dict) and "token_usage" in llm_output:
        token_usage = llm_output["token_usage"]
        if isinstance(token_usage, dict):
            input_tokens = token_usage.get("prompt_tokens", 0) or 0
            output_tokens = token_usage.get("completion_tokens", 0) or 0
            if input_tokens or output_tokens:
                return Usage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                )

    # Iterate generations for message-level and generation_info extraction
    generations = getattr(response, "generations", None) or []
    for generation_list in generations:
        for generation in generation_list:
            # Strategy 2: delegate to extract_usage_from_message() for standard paths
            message = getattr(generation, "message", None)
            if message is not None:
                usage = extract_usage_from_message(message)
                if usage:
                    return usage

            # Strategy 3: generation_info fallback (older Anthropic adapters)
            gen_info = getattr(generation, "generation_info", None) or {}
            if isinstance(gen_info, dict):
                usage_dict = gen_info.get("token_usage") or gen_info.get("usage")
                if isinstance(usage_dict, dict):
                    input_tokens = usage_dict.get("prompt_tokens") or usage_dict.get("input_tokens") or 0
                    output_tokens = usage_dict.get("completion_tokens") or usage_dict.get("output_tokens") or 0
                    if input_tokens or output_tokens:
                        return Usage(
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            total_tokens=input_tokens + output_tokens,
                        )

    return None