def _convert_dict_to_message(_dict: Mapping[str, Any]) -> BaseMessage:  # noqa: C901
    """Convert an OpenRouter API response message dict to a LangChain message.

    Extracts tool calls, reasoning content, and maps roles to the appropriate
    LangChain message type (`HumanMessage`, `AIMessage`, `SystemMessage`,
    `ToolMessage`, or `ChatMessage`).

    Args:
        _dict: The message dictionary from the API response.

    Returns:
        The corresponding LangChain message.
    """
    id_ = _dict.get("id")
    role = _dict.get("role")
    if role == "user":
        return HumanMessage(content=_dict.get("content", ""))
    if role == "assistant":
        content = _dict.get("content", "") or ""
        additional_kwargs: dict = {}
        if reasoning := _dict.get("reasoning"):
            additional_kwargs["reasoning_content"] = reasoning
        if reasoning_details := _dict.get("reasoning_details"):
            additional_kwargs["reasoning_details"] = reasoning_details
        tool_calls = []
        invalid_tool_calls = []
        if raw_tool_calls := _dict.get("tool_calls"):
            for raw_tool_call in raw_tool_calls:
                try:
                    tool_calls.append(parse_tool_call(raw_tool_call, return_id=True))
                except Exception as e:  # noqa: BLE001, PERF203
                    invalid_tool_calls.append(
                        make_invalid_tool_call(raw_tool_call, str(e))
                    )
        return AIMessage(
            content=content,
            id=id_,
            additional_kwargs=additional_kwargs,
            tool_calls=tool_calls,
            invalid_tool_calls=invalid_tool_calls,
            response_metadata={"model_provider": "openrouter"},
        )
    if role == "system":
        return SystemMessage(content=_dict.get("content", ""))
    if role == "tool":
        additional_kwargs = {}
        if "name" in _dict:
            additional_kwargs["name"] = _dict["name"]
        return ToolMessage(
            content=_dict.get("content", ""),
            tool_call_id=_dict.get("tool_call_id"),
            additional_kwargs=additional_kwargs,
        )
    if role is None:
        msg = (
            f"OpenRouter response message is missing the 'role' field. "
            f"Message keys: {list(_dict.keys())}"
        )
        raise ValueError(msg)
    warnings.warn(
        f"Unrecognized message role '{role}' from OpenRouter. "
        f"Falling back to ChatMessage.",
        stacklevel=2,
    )
    return ChatMessage(content=_dict.get("content", ""), role=role)