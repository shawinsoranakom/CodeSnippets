def _convert_chunk_to_message_chunk(  # noqa: C901, PLR0911, PLR0912
    chunk: Mapping[str, Any], default_class: type[BaseMessageChunk]
) -> BaseMessageChunk:
    """Convert a streaming chunk dict to a LangChain message chunk.

    Args:
        chunk: The streaming chunk dictionary.
        default_class: Default message chunk class.

    Returns:
        The LangChain message chunk.
    """
    choice = chunk["choices"][0]
    _dict = choice.get("delta", {})
    role = cast("str", _dict.get("role"))
    content = cast("str", _dict.get("content") or "")
    additional_kwargs: dict = {}
    tool_call_chunks: list = []

    if raw_tool_calls := _dict.get("tool_calls"):
        for rtc in raw_tool_calls:
            try:
                tool_call_chunks.append(
                    tool_call_chunk(
                        name=rtc["function"].get("name"),
                        args=rtc["function"].get("arguments"),
                        id=rtc.get("id"),
                        index=rtc["index"],
                    )
                )
            except (KeyError, TypeError, AttributeError):  # noqa: PERF203
                warnings.warn(
                    f"Skipping malformed tool call chunk during streaming: "
                    f"unexpected structure in {rtc!r}.",
                    stacklevel=2,
                )

    if role == "user" or default_class == HumanMessageChunk:
        return HumanMessageChunk(content=content)
    if role == "assistant" or default_class == AIMessageChunk:
        if reasoning := _dict.get("reasoning"):
            additional_kwargs["reasoning_content"] = reasoning
        if reasoning_details := _dict.get("reasoning_details"):
            additional_kwargs["reasoning_details"] = reasoning_details
        usage_metadata = None
        response_metadata: dict[str, Any] = {"model_provider": "openrouter"}
        if usage := chunk.get("usage"):
            usage_metadata = _create_usage_metadata(usage)
            # Surface OpenRouter cost data in response_metadata
            if "cost" in usage:
                response_metadata["cost"] = usage["cost"]
            if "cost_details" in usage:
                response_metadata["cost_details"] = usage["cost_details"]
        return AIMessageChunk(
            content=content,
            additional_kwargs=additional_kwargs,
            tool_call_chunks=tool_call_chunks,  # type: ignore[arg-type]
            usage_metadata=usage_metadata,  # type: ignore[arg-type]
            response_metadata=response_metadata,
        )
    if role == "system" or default_class == SystemMessageChunk:
        return SystemMessageChunk(content=content)
    if role == "tool" or default_class == ToolMessageChunk:
        return ToolMessageChunk(
            content=content, tool_call_id=_dict.get("tool_call_id", "")
        )
    if role:
        warnings.warn(
            f"Unrecognized streaming chunk role '{role}' from OpenRouter. "
            f"Falling back to ChatMessageChunk.",
            stacklevel=2,
        )
        return ChatMessageChunk(content=content, role=role)
    if default_class is ChatMessageChunk:
        return ChatMessageChunk(content=content, role=role or "")
    return default_class(content=content)