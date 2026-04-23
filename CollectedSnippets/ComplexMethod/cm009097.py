def _convert_responses_chunk_to_generation_chunk(
    chunk: Any,
    current_index: int,  # index in content
    current_output_index: int,  # index in Response output
    current_sub_index: int,  # index of content block in output item
    schema: type[_BM] | None = None,
    metadata: dict | None = None,
    has_reasoning: bool = False,
    output_version: str | None = None,
) -> tuple[int, int, int, ChatGenerationChunk | None]:
    def _advance(output_idx: int, sub_idx: int | None = None) -> None:
        """Advance indexes tracked during streaming.

        Example: we stream a response item of the form:

        ```python
        {
            "type": "message",  # output_index 0
            "role": "assistant",
            "id": "msg_123",
            "content": [
                {"type": "output_text", "text": "foo"},  # sub_index 0
                {"type": "output_text", "text": "bar"},  # sub_index 1
            ],
        }
        ```

        This is a single item with a shared `output_index` and two sub-indexes, one
        for each content block.

        This will be processed into an `AIMessage` with two text blocks:

        ```python
        AIMessage(
            [
                {"type": "text", "text": "foo", "id": "msg_123"},  # index 0
                {"type": "text", "text": "bar", "id": "msg_123"},  # index 1
            ]
        )
        ```

        This function just identifies updates in output or sub-indexes and increments
        the current index accordingly.
        """
        nonlocal current_index, current_output_index, current_sub_index
        if sub_idx is None:
            if current_output_index != output_idx:
                current_index += 1
        else:
            if (current_output_index != output_idx) or (current_sub_index != sub_idx):
                current_index += 1
            current_sub_index = sub_idx
        current_output_index = output_idx

    if output_version is None:
        # Sentinel value of None lets us know if output_version is set explicitly.
        # Explicitly setting `output_version="responses/v1"` separately enables the
        # Responses API.
        output_version = "responses/v1"

    content = []
    tool_call_chunks: list = []
    additional_kwargs: dict = {}
    response_metadata = metadata or {}
    response_metadata["model_provider"] = "openai"
    usage_metadata = None
    chunk_position: Literal["last"] | None = None
    id = None
    if chunk.type == "response.output_text.delta":
        _advance(chunk.output_index, chunk.content_index)
        content.append({"type": "text", "text": chunk.delta, "index": current_index})
    elif chunk.type == "response.output_text.annotation.added":
        _advance(chunk.output_index, chunk.content_index)
        if isinstance(chunk.annotation, dict):
            # Appears to be a breaking change in openai==1.82.0
            annotation = chunk.annotation
        else:
            annotation = chunk.annotation.model_dump(exclude_none=True, mode="json")

        content.append(
            {
                "type": "text",
                "annotations": [_format_annotation_to_lc(annotation)],
                "index": current_index,
            }
        )
    elif chunk.type == "response.output_text.done":
        _advance(chunk.output_index, chunk.content_index)
        content.append(
            {
                "type": "text",
                "text": "",
                "id": chunk.item_id,
                "index": current_index,
            }
        )
    elif chunk.type == "response.created":
        response = _coerce_chunk_response(chunk.response)
        id = response.id
        response_metadata["id"] = response.id  # Backwards compatibility
    elif chunk.type in ("response.completed", "response.incomplete"):
        response = _coerce_chunk_response(chunk.response)
        msg = cast(
            AIMessage,
            (
                _construct_lc_result_from_responses_api(
                    response, schema=schema, output_version=output_version
                )
                .generations[0]
                .message
            ),
        )
        if parsed := msg.additional_kwargs.get("parsed"):
            additional_kwargs["parsed"] = parsed
        usage_metadata = msg.usage_metadata
        response_metadata = {
            k: v for k, v in msg.response_metadata.items() if k != "id"
        }
        chunk_position = "last"
    elif chunk.type == "response.output_item.added" and chunk.item.type == "message":
        if output_version == "v0":
            id = chunk.item.id
        elif phase := getattr(chunk.item, "phase", None):
            _advance(chunk.output_index, 0)
            content.append(
                {
                    "type": "text",
                    "text": "",
                    "phase": phase,
                    "index": current_index,
                }
            )
        else:
            pass
    elif (
        chunk.type == "response.output_item.added"
        and chunk.item.type == "function_call"
    ):
        _advance(chunk.output_index)
        tool_call_chunks.append(
            {
                "type": "tool_call_chunk",
                "name": chunk.item.name,
                "args": chunk.item.arguments,
                "id": chunk.item.call_id,
                "index": current_index,
            }
        )
        function_call_content: dict = {
            "type": "function_call",
            "name": chunk.item.name,
            "arguments": chunk.item.arguments,
            "call_id": chunk.item.call_id,
            "id": chunk.item.id,
            "index": current_index,
        }
        if getattr(chunk.item, "namespace", None) is not None:
            function_call_content["namespace"] = chunk.item.namespace
        content.append(function_call_content)
    elif chunk.type == "response.output_item.done" and chunk.item.type in (
        "compaction",
        "web_search_call",
        "file_search_call",
        "computer_call",
        "code_interpreter_call",
        "mcp_call",
        "mcp_list_tools",
        "mcp_approval_request",
        "image_generation_call",
        "tool_search_call",
        "tool_search_output",
    ):
        _advance(chunk.output_index)
        tool_output = chunk.item.model_dump(exclude_none=True, mode="json")
        tool_output["index"] = current_index
        content.append(tool_output)
    elif (
        chunk.type == "response.output_item.done"
        and chunk.item.type == "custom_tool_call"
    ):
        _advance(chunk.output_index)
        tool_output = chunk.item.model_dump(exclude_none=True, mode="json")
        tool_output["index"] = current_index
        content.append(tool_output)
        tool_call_chunks.append(
            {
                "type": "tool_call_chunk",
                "name": chunk.item.name,
                "args": json.dumps({"__arg1": chunk.item.input}),
                "id": chunk.item.call_id,
                "index": current_index,
            }
        )
    elif chunk.type == "response.function_call_arguments.delta":
        _advance(chunk.output_index)
        tool_call_chunks.append(
            {"type": "tool_call_chunk", "args": chunk.delta, "index": current_index}
        )
        content.append(
            {"type": "function_call", "arguments": chunk.delta, "index": current_index}
        )
    elif chunk.type == "response.refusal.done":
        content.append({"type": "refusal", "refusal": chunk.refusal})
    elif chunk.type == "response.output_item.added" and chunk.item.type == "reasoning":
        _advance(chunk.output_index)
        current_sub_index = 0
        reasoning = chunk.item.model_dump(exclude_none=True, mode="json")
        reasoning["index"] = current_index
        content.append(reasoning)
    elif chunk.type == "response.reasoning_summary_part.added":
        _advance(chunk.output_index)
        content.append(
            {
                # langchain-core uses the `index` key to aggregate text blocks.
                "summary": [
                    {"index": chunk.summary_index, "type": "summary_text", "text": ""}
                ],
                "index": current_index,
                "type": "reasoning",
                "id": chunk.item_id,
            }
        )
    elif chunk.type == "response.image_generation_call.partial_image":
        # Partial images are not supported yet.
        pass
    elif chunk.type == "response.reasoning_summary_text.delta":
        _advance(chunk.output_index)
        content.append(
            {
                "summary": [
                    {
                        "index": chunk.summary_index,
                        "type": "summary_text",
                        "text": chunk.delta,
                    }
                ],
                "index": current_index,
                "type": "reasoning",
            }
        )
    else:
        return current_index, current_output_index, current_sub_index, None

    message = AIMessageChunk(
        content=content,  # type: ignore[arg-type]
        tool_call_chunks=tool_call_chunks,
        usage_metadata=usage_metadata,
        response_metadata=response_metadata,
        additional_kwargs=additional_kwargs,
        id=id,
        chunk_position=chunk_position,
    )
    if output_version == "v0":
        message = cast(
            AIMessageChunk,
            _convert_to_v03_ai_message(message, has_reasoning=has_reasoning),
        )

    return (
        current_index,
        current_output_index,
        current_sub_index,
        ChatGenerationChunk(message=message),
    )