def _convert_from_v03_ai_message(message: AIMessage) -> AIMessage:
    """Convert v0 AIMessage into `output_version="responses/v1"` format."""
    # Only update ChatOpenAI v0.3 AIMessages
    is_chatopenai_v03 = (
        isinstance(message.content, list)
        and all(isinstance(b, dict) for b in message.content)
    ) and (
        any(
            item in message.additional_kwargs
            for item in [
                "reasoning",
                "tool_outputs",
                "refusal",
                _FUNCTION_CALL_IDS_MAP_KEY,
            ]
        )
        or (
            isinstance(message.id, str)
            and message.id.startswith("msg_")
            and (response_id := message.response_metadata.get("id"))
            and isinstance(response_id, str)
            and response_id.startswith("resp_")
        )
    )
    if not is_chatopenai_v03:
        return message

    content_order = [
        "reasoning",
        "code_interpreter_call",
        "mcp_call",
        "image_generation_call",
        "text",
        "refusal",
        "function_call",
        "computer_call",
        "mcp_list_tools",
        "mcp_approval_request",
        # N. B. "web_search_call" and "file_search_call" were not passed back in
        # in v0.3
    ]

    # Build a bucket for every known block type
    buckets: dict[str, list] = {key: [] for key in content_order}
    unknown_blocks = []

    # Reasoning
    if reasoning := message.additional_kwargs.get("reasoning"):
        if "type" not in reasoning:
            reasoning = {**reasoning, "type": "reasoning"}
        buckets["reasoning"].append(reasoning)

    # Refusal
    if refusal := message.additional_kwargs.get("refusal"):
        buckets["refusal"].append({"type": "refusal", "refusal": refusal})

    # Text
    for block in message.content:
        if isinstance(block, dict) and block.get("type") == "text":
            block_copy = block.copy()
            if isinstance(message.id, str) and message.id.startswith("msg_"):
                block_copy["id"] = message.id
            buckets["text"].append(block_copy)
        else:
            unknown_blocks.append(block)

    # Function calls
    function_call_ids = message.additional_kwargs.get(_FUNCTION_CALL_IDS_MAP_KEY)
    if (
        isinstance(message, AIMessageChunk)
        and len(message.tool_call_chunks) == 1
        and message.chunk_position != "last"
    ):
        # Isolated chunk
        tool_call_chunk = message.tool_call_chunks[0]
        function_call = {
            "type": "function_call",
            "name": tool_call_chunk.get("name"),
            "arguments": tool_call_chunk.get("args"),
            "call_id": tool_call_chunk.get("id"),
        }
        if function_call_ids is not None and (
            id_ := function_call_ids.get(tool_call_chunk.get("id"))
        ):
            function_call["id"] = id_
        buckets["function_call"].append(function_call)
    else:
        for tool_call in message.tool_calls:
            function_call = {
                "type": "function_call",
                "name": tool_call["name"],
                "arguments": json.dumps(tool_call["args"], ensure_ascii=False),
                "call_id": tool_call["id"],
            }
            if function_call_ids is not None and (
                id_ := function_call_ids.get(tool_call["id"])
            ):
                function_call["id"] = id_
            buckets["function_call"].append(function_call)

    # Tool outputs
    tool_outputs = message.additional_kwargs.get("tool_outputs", [])
    for block in tool_outputs:
        if isinstance(block, dict) and (key := block.get("type")) and key in buckets:
            buckets[key].append(block)
        else:
            unknown_blocks.append(block)

    # Re-assemble the content list in the canonical order
    new_content = []
    for key in content_order:
        new_content.extend(buckets[key])
    new_content.extend(unknown_blocks)

    new_additional_kwargs = dict(message.additional_kwargs)
    new_additional_kwargs.pop("reasoning", None)
    new_additional_kwargs.pop("refusal", None)
    new_additional_kwargs.pop("tool_outputs", None)

    if "id" in message.response_metadata:
        new_id = message.response_metadata["id"]
    else:
        new_id = message.id

    return message.model_copy(
        update={
            "content": new_content,
            "additional_kwargs": new_additional_kwargs,
            "id": new_id,
        },
        deep=False,
    )