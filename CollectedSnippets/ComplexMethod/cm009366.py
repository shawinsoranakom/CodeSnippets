def _convert_chunk_to_message_chunk(
    chunk: Mapping[str, Any], default_class: type[BaseMessageChunk]
) -> BaseMessageChunk:
    choice = chunk["choices"][0]
    _dict = choice["delta"]
    role = cast("str", _dict.get("role"))
    content = cast("str", _dict.get("content") or "")
    additional_kwargs: dict = {}
    if _dict.get("function_call"):
        function_call = dict(_dict["function_call"])
        if "name" in function_call and function_call["name"] is None:
            function_call["name"] = ""
        additional_kwargs["function_call"] = function_call
    if _dict.get("tool_calls"):
        # Groq sends 'null' (JSON null) for tools with no arguments, but we
        # expect '{}' (empty JSON object) to represent empty arguments
        tool_calls = _dict["tool_calls"]
        for tool_call in tool_calls:
            if (
                tool_call.get("function")
                and tool_call["function"].get("arguments") == "null"
            ):
                tool_call["function"]["arguments"] = "{}"
        additional_kwargs["tool_calls"] = tool_calls

    if role == "user" or default_class == HumanMessageChunk:
        return HumanMessageChunk(content=content)
    if role == "assistant" or default_class == AIMessageChunk:
        if reasoning := _dict.get("reasoning"):
            additional_kwargs["reasoning_content"] = reasoning
        if executed_tools := _dict.get("executed_tools"):
            additional_kwargs["executed_tools"] = []
            for executed_tool in executed_tools:
                if executed_tool.get("output"):
                    # Tool output duplicates query and other server tool call data
                    additional_kwargs["executed_tools"].append(
                        {
                            k: executed_tool[k]
                            for k in ("index", "output")
                            if k in executed_tool
                        }
                    )
                else:
                    additional_kwargs["executed_tools"].append(
                        {k: executed_tool[k] for k in executed_tool if k != "output"}
                    )
        if usage := (chunk.get("x_groq") or {}).get("usage"):
            usage_metadata = _create_usage_metadata(usage)
        else:
            usage_metadata = None
        return AIMessageChunk(
            content=content,
            additional_kwargs=additional_kwargs,
            usage_metadata=usage_metadata,  # type: ignore[arg-type]
            response_metadata={"model_provider": "groq"},
        )
    if role == "system" or default_class == SystemMessageChunk:
        return SystemMessageChunk(content=content)
    if role == "function" or default_class == FunctionMessageChunk:
        return FunctionMessageChunk(content=content, name=_dict["name"])
    if role == "tool" or default_class == ToolMessageChunk:
        return ToolMessageChunk(content=content, tool_call_id=_dict["tool_call_id"])
    if role or default_class == ChatMessageChunk:
        return ChatMessageChunk(content=content, role=role)
    return default_class(content=content)