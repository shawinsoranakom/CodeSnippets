def _convert_chunk_to_message_chunk(
    chunk: dict,
    default_class: type[BaseMessageChunk],
    index: int,
    index_type: str,
    output_version: str | None,
) -> tuple[BaseMessageChunk, int, str]:
    _choice = chunk["choices"][0]
    _delta = _choice["delta"]
    role = _delta.get("role")
    content = _delta.get("content") or ""
    if output_version == "v1" and isinstance(content, str):
        content = [{"type": "text", "text": content}]
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if "type" in block and block["type"] != index_type:
                    index_type = block["type"]
                    index = index + 1
                if "index" not in block:
                    block["index"] = index
                if block.get("type") == "thinking" and isinstance(
                    block.get("thinking"), list
                ):
                    for sub_block in block["thinking"]:
                        if isinstance(sub_block, dict) and "index" not in sub_block:
                            sub_block["index"] = 0
    if role == "user" or default_class == HumanMessageChunk:
        return HumanMessageChunk(content=content), index, index_type
    if role == "assistant" or default_class == AIMessageChunk:
        additional_kwargs: dict = {}
        response_metadata = {}
        if raw_tool_calls := _delta.get("tool_calls"):
            additional_kwargs["tool_calls"] = raw_tool_calls
            try:
                tool_call_chunks = []
                for raw_tool_call in raw_tool_calls:
                    if not raw_tool_call.get("index") and not raw_tool_call.get("id"):
                        tool_call_id = uuid.uuid4().hex[:]
                    else:
                        tool_call_id = raw_tool_call.get("id")
                    tool_call_chunks.append(
                        tool_call_chunk(
                            name=raw_tool_call["function"].get("name"),
                            args=raw_tool_call["function"].get("arguments"),
                            id=tool_call_id,
                            index=raw_tool_call.get("index"),
                        )
                    )
            except KeyError:
                pass
        else:
            tool_call_chunks = []
        if token_usage := chunk.get("usage"):
            usage_metadata = {
                "input_tokens": token_usage.get("prompt_tokens", 0),
                "output_tokens": token_usage.get("completion_tokens", 0),
                "total_tokens": token_usage.get("total_tokens", 0),
            }
        else:
            usage_metadata = None
        if _choice.get("finish_reason") is not None and isinstance(
            chunk.get("model"), str
        ):
            response_metadata["model_name"] = chunk["model"]
            response_metadata["finish_reason"] = _choice["finish_reason"]
        return (
            AIMessageChunk(
                content=content,
                additional_kwargs=additional_kwargs,
                tool_call_chunks=tool_call_chunks,  # type: ignore[arg-type]
                usage_metadata=usage_metadata,  # type: ignore[arg-type]
                response_metadata={"model_provider": "mistralai", **response_metadata},
            ),
            index,
            index_type,
        )
    if role == "system" or default_class == SystemMessageChunk:
        return SystemMessageChunk(content=content), index, index_type
    if role or default_class == ChatMessageChunk:
        return ChatMessageChunk(content=content, role=role), index, index_type
    return default_class(content=content), index, index_type