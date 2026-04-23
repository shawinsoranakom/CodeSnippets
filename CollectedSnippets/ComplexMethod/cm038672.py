async def message_stream_converter(
        self,
        generator: AsyncGenerator[str, None],
    ) -> AsyncGenerator[str, None]:
        try:

            class _ActiveBlockState:
                def __init__(self) -> None:
                    self.content_block_index = 0
                    self.block_type: str | None = None
                    self.block_index: int | None = None
                    self.block_signature: str | None = None
                    self.signature_emitted: bool = False
                    self.tool_use_id: str | None = None

                def reset(self) -> None:
                    self.block_type = None
                    self.block_index = None
                    self.block_signature = None
                    self.signature_emitted = False
                    self.tool_use_id = None

                def start(self, block: AnthropicContentBlock) -> None:
                    self.block_type = block.type
                    self.block_index = self.content_block_index
                    if block.type == "thinking":
                        self.block_signature = uuid.uuid4().hex
                        self.signature_emitted = False
                        self.tool_use_id = None
                    elif block.type == "tool_use":
                        self.block_signature = None
                        self.signature_emitted = True
                        self.tool_use_id = block.id
                    else:
                        self.block_signature = None
                        self.signature_emitted = True
                        self.tool_use_id = None

            first_item = True
            finish_reason = None
            state = _ActiveBlockState()
            # Map from tool call index to tool_use_id
            tool_index_to_id: dict[int, str] = {}

            def stop_active_block():
                events: list[str] = []
                if state.block_type is None:
                    return events
                if (
                    state.block_type == "thinking"
                    and state.block_signature is not None
                    and not state.signature_emitted
                ):
                    chunk = AnthropicStreamEvent(
                        index=state.block_index,
                        type="content_block_delta",
                        delta=AnthropicDelta(
                            type="signature_delta",
                            signature=state.block_signature,
                        ),
                    )
                    data = chunk.model_dump_json(exclude_unset=True)
                    events.append(wrap_data_with_event(data, "content_block_delta"))
                    state.signature_emitted = True
                stop_chunk = AnthropicStreamEvent(
                    index=state.block_index,
                    type="content_block_stop",
                )
                data = stop_chunk.model_dump_json(exclude_unset=True)
                events.append(wrap_data_with_event(data, "content_block_stop"))
                state.reset()
                state.content_block_index += 1
                return events

            def start_block(block: AnthropicContentBlock):
                chunk = AnthropicStreamEvent(
                    index=state.content_block_index,
                    type="content_block_start",
                    content_block=block,
                )
                data = chunk.model_dump_json(exclude_unset=True)
                event = wrap_data_with_event(data, "content_block_start")
                state.start(block)
                return event

            async for item in generator:
                if item.startswith("data:"):
                    data_str = item[5:].strip().rstrip("\n")
                    if data_str == "[DONE]":
                        stop_message = AnthropicStreamEvent(
                            type="message_stop",
                        )
                        data = stop_message.model_dump_json(
                            exclude_unset=True, exclude_none=True
                        )
                        yield wrap_data_with_event(data, "message_stop")
                    else:
                        origin_chunk = ChatCompletionStreamResponse.model_validate_json(
                            data_str
                        )

                        if first_item:
                            chunk = AnthropicStreamEvent(
                                type="message_start",
                                message=AnthropicMessagesResponse(
                                    id=origin_chunk.id,
                                    content=[],
                                    model=origin_chunk.model,
                                    stop_reason=None,
                                    stop_sequence=None,
                                    usage=AnthropicUsage(
                                        input_tokens=origin_chunk.usage.prompt_tokens
                                        if origin_chunk.usage
                                        else 0,
                                        output_tokens=0,
                                    ),
                                ),
                            )
                            first_item = False
                            data = chunk.model_dump_json(exclude_unset=True)
                            yield wrap_data_with_event(data, "message_start")
                            continue

                        # last chunk including usage info
                        if len(origin_chunk.choices) == 0:
                            for event in stop_active_block():
                                yield event
                            stop_reason = self.stop_reason_map.get(
                                finish_reason or "stop"
                            )
                            chunk = AnthropicStreamEvent(
                                type="message_delta",
                                delta=AnthropicDelta(stop_reason=stop_reason),
                                usage=AnthropicUsage(
                                    input_tokens=origin_chunk.usage.prompt_tokens
                                    if origin_chunk.usage
                                    else 0,
                                    output_tokens=origin_chunk.usage.completion_tokens
                                    if origin_chunk.usage
                                    else 0,
                                ),
                            )
                            data = chunk.model_dump_json(exclude_unset=True)
                            yield wrap_data_with_event(data, "message_delta")
                            continue

                        if origin_chunk.choices[0].finish_reason is not None:
                            finish_reason = origin_chunk.choices[0].finish_reason
                            # continue

                        # thinking / text content
                        reasoning_delta = origin_chunk.choices[0].delta.reasoning
                        if reasoning_delta is not None:
                            if reasoning_delta == "":
                                pass
                            else:
                                if state.block_type != "thinking":
                                    for event in stop_active_block():
                                        yield event
                                    start_event = start_block(
                                        AnthropicContentBlock(
                                            type="thinking", thinking=""
                                        )
                                    )
                                    yield start_event
                                chunk = AnthropicStreamEvent(
                                    index=(
                                        state.block_index
                                        if state.block_index is not None
                                        else state.content_block_index
                                    ),
                                    type="content_block_delta",
                                    delta=AnthropicDelta(
                                        type="thinking_delta",
                                        thinking=reasoning_delta,
                                    ),
                                )
                                data = chunk.model_dump_json(exclude_unset=True)
                                yield wrap_data_with_event(data, "content_block_delta")

                        if origin_chunk.choices[0].delta.content is not None:
                            if origin_chunk.choices[0].delta.content == "":
                                pass
                            else:
                                if state.block_type != "text":
                                    for event in stop_active_block():
                                        yield event
                                    start_event = start_block(
                                        AnthropicContentBlock(type="text", text="")
                                    )
                                    yield start_event
                                chunk = AnthropicStreamEvent(
                                    index=(
                                        state.block_index
                                        if state.block_index is not None
                                        else state.content_block_index
                                    ),
                                    type="content_block_delta",
                                    delta=AnthropicDelta(
                                        type="text_delta",
                                        text=origin_chunk.choices[0].delta.content,
                                    ),
                                )
                                data = chunk.model_dump_json(exclude_unset=True)
                                yield wrap_data_with_event(data, "content_block_delta")

                        # tool calls - process all tool calls in the delta
                        if len(origin_chunk.choices[0].delta.tool_calls) > 0:
                            for tool_call in origin_chunk.choices[0].delta.tool_calls:
                                if tool_call.id is not None:
                                    # Update mapping for incremental updates
                                    tool_index_to_id[tool_call.index] = tool_call.id
                                    # Only create new block if different tool call
                                    # AND has a name
                                    tool_name = (
                                        tool_call.function.name
                                        if tool_call.function
                                        else None
                                    )
                                    if (
                                        state.tool_use_id != tool_call.id
                                        and tool_name is not None
                                    ):
                                        for event in stop_active_block():
                                            yield event
                                        start_event = start_block(
                                            AnthropicContentBlock(
                                                type="tool_use",
                                                id=tool_call.id,
                                                name=tool_name,
                                                input={},
                                            )
                                        )
                                        yield start_event
                                    # Handle initial arguments if present
                                    if (
                                        tool_call.function
                                        and tool_call.function.arguments
                                        and state.tool_use_id == tool_call.id
                                    ):
                                        chunk = AnthropicStreamEvent(
                                            index=(
                                                state.block_index
                                                if state.block_index is not None
                                                else state.content_block_index
                                            ),
                                            type="content_block_delta",
                                            delta=AnthropicDelta(
                                                type="input_json_delta",
                                                partial_json=tool_call.function.arguments,
                                            ),
                                        )
                                        data = chunk.model_dump_json(exclude_unset=True)
                                        yield wrap_data_with_event(
                                            data, "content_block_delta"
                                        )
                                else:
                                    # Incremental update - use index to find tool_use_id
                                    tool_use_id = tool_index_to_id.get(tool_call.index)
                                    if (
                                        tool_use_id is not None
                                        and tool_call.function
                                        and tool_call.function.arguments
                                        and state.tool_use_id == tool_use_id
                                    ):
                                        chunk = AnthropicStreamEvent(
                                            index=(
                                                state.block_index
                                                if state.block_index is not None
                                                else state.content_block_index
                                            ),
                                            type="content_block_delta",
                                            delta=AnthropicDelta(
                                                type="input_json_delta",
                                                partial_json=tool_call.function.arguments,
                                            ),
                                        )
                                        data = chunk.model_dump_json(exclude_unset=True)
                                        yield wrap_data_with_event(
                                            data, "content_block_delta"
                                        )
                            continue
                else:
                    error_response = AnthropicStreamEvent(
                        type="error",
                        error=AnthropicError(
                            type="internal_error",
                            message="Invalid data format received",
                        ),
                    )
                    data = error_response.model_dump_json(exclude_unset=True)
                    yield wrap_data_with_event(data, "error")

        except Exception as e:
            logger.exception("Error in message stream converter.")
            error_response = AnthropicStreamEvent(
                type="error",
                error=AnthropicError(type="internal_error", message=str(e)),
            )
            data = error_response.model_dump_json(exclude_unset=True)
            yield wrap_data_with_event(data, "error")