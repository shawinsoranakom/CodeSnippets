async def _process_simple_streaming_events(
        self,
        request: ResponsesRequest,
        sampling_params: SamplingParams,
        result_generator: AsyncIterator[ConversationContext | None],
        context: ConversationContext,
        model_name: str,
        tokenizer: TokenizerLike,
        request_metadata: RequestResponseMetadata,
        created_time: int,
        _increment_sequence_number_and_return: Callable[
            [StreamingResponsesResponse], StreamingResponsesResponse
        ],
    ) -> AsyncGenerator[StreamingResponsesResponse, None]:
        current_content_index = 0
        current_output_index = 0
        current_item_id = ""
        current_tool_call_index: int | None = None
        parser = self.parser(tokenizer, request.tools) if self.parser else None
        first_delta_sent = False
        previous_delta_messages: list[DeltaMessage] = []
        async for ctx in result_generator:
            assert isinstance(ctx, SimpleContext)
            if ctx.last_output is None:
                continue
            if ctx.last_output.outputs:
                output = ctx.last_output.outputs[0]
                # finish_reason='error' indicates a retryable error
                self._raise_if_error(output.finish_reason, request.request_id)
                delta_text = output.text
                delta_token_ids = as_list(output.token_ids)

                if parser:
                    delta_message = parser.parse_delta(
                        delta_text=delta_text,
                        delta_token_ids=delta_token_ids,
                        request=request,
                        prompt_token_ids=ctx.last_output.prompt_token_ids,
                    )
                else:
                    delta_message = DeltaMessage(
                        content=output.text,
                    )
                if not delta_message:
                    continue
                tool_call_item_started = False
                if not first_delta_sent:
                    current_item_id = random_uuid()
                    if delta_message.tool_calls:
                        current_tool_call_id = f"call_{random_uuid()}"
                        assert len(delta_message.tool_calls) == 1, (
                            "Multiple tool calls in one delta is not supported"
                        )
                        assert delta_message.tool_calls[0].function is not None, (
                            "Tool call without function is not supported"
                        )
                        assert delta_message.tool_calls[0].function.name is not None, (
                            "Tool call without function name is not supported"
                        )
                        current_tool_call_name = delta_message.tool_calls[
                            0
                        ].function.name
                        current_tool_call_index = delta_message.tool_calls[0].index
                        yield _increment_sequence_number_and_return(
                            ResponseOutputItemAddedEvent(
                                type="response.output_item.added",
                                sequence_number=-1,
                                output_index=current_output_index,
                                item=ResponseFunctionToolCallItem(
                                    type="function_call",
                                    id=current_item_id,
                                    call_id=current_tool_call_id,
                                    name=current_tool_call_name,
                                    arguments="",
                                    status="in_progress",
                                ),
                            )
                        )
                        tool_call_item_started = True
                    elif delta_message.reasoning:
                        yield _increment_sequence_number_and_return(
                            ResponseOutputItemAddedEvent(
                                type="response.output_item.added",
                                sequence_number=-1,
                                output_index=current_output_index,
                                item=ResponseReasoningItem(
                                    type="reasoning",
                                    id=current_item_id,
                                    summary=[],
                                    status="in_progress",
                                ),
                            )
                        )
                        yield _increment_sequence_number_and_return(
                            ResponseReasoningPartAddedEvent(
                                type="response.reasoning_part.added",
                                sequence_number=-1,
                                output_index=current_output_index,
                                item_id=current_item_id,
                                content_index=current_content_index,
                                part=ResponseReasoningTextContent(
                                    text="",
                                    type="reasoning_text",
                                ),
                            )
                        )
                    elif not delta_message.tool_calls:
                        yield _increment_sequence_number_and_return(
                            ResponseOutputItemAddedEvent(
                                type="response.output_item.added",
                                sequence_number=-1,
                                output_index=current_output_index,
                                item=ResponseOutputMessage(
                                    id=current_item_id,
                                    type="message",
                                    role="assistant",
                                    content=[],
                                    status="in_progress",
                                ),
                            )
                        )
                        yield _increment_sequence_number_and_return(
                            ResponseContentPartAddedEvent(
                                type="response.content_part.added",
                                sequence_number=-1,
                                output_index=current_output_index,
                                item_id=current_item_id,
                                content_index=current_content_index,
                                part=ResponseOutputText(
                                    type="output_text",
                                    text="",
                                    annotations=[],
                                    logprobs=[],
                                ),
                            )
                        )
                    first_delta_sent = True

                # check delta message and previous delta message are
                # same as content or reasoning content
                if (
                    previous_delta_messages
                    and previous_delta_messages[-1].reasoning is not None
                    and delta_message.content is not None
                ):
                    # from reasoning to normal content, send done
                    # event for reasoning
                    reason_content = "".join(
                        pm.reasoning
                        for pm in previous_delta_messages
                        if pm.reasoning is not None
                    )

                    # delta message could have both reasoning and
                    # content. Include current delta's reasoning in the
                    # finalization since it may carry the tail end of
                    # reasoning text (e.g. when reasoning end and
                    # content start arrive in the same delta).
                    if delta_message.reasoning is not None:
                        yield _increment_sequence_number_and_return(
                            ResponseReasoningTextDeltaEvent(
                                type="response.reasoning_text.delta",
                                sequence_number=-1,
                                content_index=current_content_index,
                                output_index=current_output_index,
                                item_id=current_item_id,
                                delta=delta_message.reasoning,
                            )
                        )
                        reason_content += delta_message.reasoning
                        delta_message = DeltaMessage(content=delta_message.content)

                    yield _increment_sequence_number_and_return(
                        ResponseReasoningTextDoneEvent(
                            type="response.reasoning_text.done",
                            item_id=current_item_id,
                            sequence_number=-1,
                            output_index=current_output_index,
                            content_index=current_content_index,
                            text=reason_content,
                        )
                    )
                    yield _increment_sequence_number_and_return(
                        ResponseReasoningPartDoneEvent(
                            type="response.reasoning_part.done",
                            sequence_number=-1,
                            item_id=current_item_id,
                            output_index=current_output_index,
                            content_index=current_content_index,
                            part=ResponseReasoningTextContent(
                                text=reason_content,
                                type="reasoning_text",
                            ),
                        )
                    )
                    current_content_index = 0
                    reasoning_item = ResponseReasoningItem(
                        type="reasoning",
                        content=[
                            ResponseReasoningTextContent(
                                text=reason_content,
                                type="reasoning_text",
                            ),
                        ],
                        status="completed",
                        id=current_item_id,
                        summary=[],
                    )
                    yield _increment_sequence_number_and_return(
                        ResponseOutputItemDoneEvent(
                            type="response.output_item.done",
                            sequence_number=-1,
                            output_index=current_output_index,
                            item=reasoning_item,
                        )
                    )
                    current_output_index += 1
                    current_item_id = str(uuid.uuid4())
                    yield _increment_sequence_number_and_return(
                        ResponseOutputItemAddedEvent(
                            type="response.output_item.added",
                            sequence_number=-1,
                            output_index=current_output_index,
                            item=ResponseOutputMessage(
                                id=current_item_id,
                                type="message",
                                role="assistant",
                                content=[],
                                status="in_progress",
                            ),
                        )
                    )
                    yield _increment_sequence_number_and_return(
                        ResponseContentPartAddedEvent(
                            type="response.content_part.added",
                            sequence_number=-1,
                            output_index=current_output_index,
                            item_id=current_item_id,
                            content_index=current_content_index,
                            part=ResponseOutputText(
                                type="output_text",
                                text="",
                                annotations=[],
                                logprobs=[],
                            ),
                        )
                    )
                    # reset previous delta messages
                    previous_delta_messages = []
                if delta_message.tool_calls and delta_message.tool_calls[0].function:
                    tool_call = delta_message.tool_calls[0]
                    tool_call_function = tool_call.function
                    if (
                        current_tool_call_index is not None
                        and tool_call.index is not None
                        and tool_call.index != current_tool_call_index
                        and tool_call_function is not None
                        and tool_call_function.name is not None
                    ):
                        # From one tool call to another, finalize the previous
                        # function-call item before opening the next one.
                        parts = []
                        for pm in previous_delta_messages:
                            if pm.tool_calls:
                                previous_tool_call = pm.tool_calls[0]
                                if previous_tool_call.function is not None:
                                    parts.append(
                                        previous_tool_call.function.arguments or ""
                                    )

                        tool_call_arguments = "".join(parts)
                        yield _increment_sequence_number_and_return(
                            ResponseFunctionCallArgumentsDoneEvent(
                                type="response.function_call_arguments.done",
                                sequence_number=-1,
                                output_index=current_output_index,
                                item_id=current_item_id,
                                arguments=tool_call_arguments,
                                name=current_tool_call_name,
                            )
                        )
                        function_call_item = ResponseFunctionToolCall(
                            type="function_call",
                            name=current_tool_call_name,
                            arguments=tool_call_arguments,
                            status="completed",
                            id=current_item_id,
                            call_id=current_tool_call_id,
                        )
                        yield _increment_sequence_number_and_return(
                            ResponseOutputItemDoneEvent(
                                type="response.output_item.done",
                                sequence_number=-1,
                                output_index=current_output_index,
                                item=function_call_item,
                            )
                        )
                        # Reset previous delta messages so the next tool call
                        # does not reuse arguments from the completed item.
                        previous_delta_messages = []
                        current_output_index += 1
                        current_item_id = random_uuid()
                        current_tool_call_name = tool_call_function.name
                        current_tool_call_id = f"call_{random_uuid()}"
                        current_tool_call_index = tool_call.index
                        yield _increment_sequence_number_and_return(
                            ResponseOutputItemAddedEvent(
                                type="response.output_item.added",
                                sequence_number=-1,
                                output_index=current_output_index,
                                item=ResponseFunctionToolCallItem(
                                    type="function_call",
                                    id=current_item_id,
                                    call_id=current_tool_call_id,
                                    name=current_tool_call_name,
                                    arguments="",
                                    status="in_progress",
                                ),
                            )
                        )
                        current_content_index = 0
                        tool_call_item_started = True

                    if delta_message.tool_calls[0].function.arguments:
                        yield _increment_sequence_number_and_return(
                            ResponseFunctionCallArgumentsDeltaEvent(
                                type="response.function_call_arguments.delta",
                                sequence_number=-1,
                                output_index=current_output_index,
                                item_id=current_item_id,
                                delta=delta_message.tool_calls[0].function.arguments,
                            )
                        )
                    # tool call initiated with no arguments
                    elif (
                        delta_message.tool_calls[0].function.name
                        and not tool_call_item_started
                    ):
                        # send done with current content part
                        # and add new function call item
                        yield _increment_sequence_number_and_return(
                            ResponseTextDoneEvent(
                                type="response.output_text.done",
                                sequence_number=-1,
                                output_index=current_output_index,
                                content_index=current_content_index,
                                text="",
                                logprobs=[],
                                item_id=current_item_id,
                            )
                        )
                        yield _increment_sequence_number_and_return(
                            ResponseContentPartDoneEvent(
                                type="response.content_part.done",
                                sequence_number=-1,
                                item_id=current_item_id,
                                output_index=current_output_index,
                                content_index=current_content_index,
                                part=ResponseOutputText(
                                    type="output_text",
                                    text="",
                                    annotations=[],
                                    logprobs=[],
                                ),
                            )
                        )
                        yield _increment_sequence_number_and_return(
                            ResponseOutputItemDoneEvent(
                                type="response.output_item.done",
                                sequence_number=-1,
                                output_index=current_output_index,
                                item=ResponseOutputMessage(
                                    id=current_item_id,
                                    type="message",
                                    role="assistant",
                                    content=[],
                                    status="completed",
                                ),
                            )
                        )
                        current_output_index += 1
                        current_item_id = random_uuid()
                        current_tool_call_name = delta_message.tool_calls[
                            0
                        ].function.name
                        current_tool_call_id = f"call_{random_uuid()}"
                        current_tool_call_index = delta_message.tool_calls[0].index
                        yield _increment_sequence_number_and_return(
                            ResponseOutputItemAddedEvent(
                                type="response.output_item.added",
                                sequence_number=-1,
                                output_index=current_output_index,
                                item=ResponseFunctionToolCallItem(
                                    type="function_call",
                                    id=current_item_id,
                                    call_id=current_tool_call_id,
                                    name=current_tool_call_name,
                                    arguments="",
                                    status="in_progress",
                                ),
                            )
                        )
                        # skip content part for tool call
                        current_content_index = 1
                        continue
                elif delta_message.reasoning is not None:
                    yield _increment_sequence_number_and_return(
                        ResponseReasoningTextDeltaEvent(
                            type="response.reasoning_text.delta",
                            sequence_number=-1,
                            content_index=current_content_index,
                            output_index=current_output_index,
                            item_id=current_item_id,
                            delta=delta_message.reasoning,
                        )
                    )
                elif delta_message.content:
                    yield _increment_sequence_number_and_return(
                        ResponseTextDeltaEvent(
                            type="response.output_text.delta",
                            sequence_number=-1,
                            content_index=current_content_index,
                            output_index=current_output_index,
                            item_id=current_item_id,
                            delta=delta_message.content,
                            logprobs=(
                                self._create_stream_response_logprobs(
                                    token_ids=output.token_ids,
                                    logprobs=output.logprobs,
                                    tokenizer=tokenizer,
                                    top_logprobs=request.top_logprobs,
                                )
                                if request.is_include_output_logprobs()
                                else []
                            ),
                        )
                    )

                previous_delta_messages.append(delta_message)

        if previous_delta_messages:
            parts = []
            for pm in previous_delta_messages:
                if pm.tool_calls:
                    assert len(pm.tool_calls) == 1, (
                        "Multiple tool calls in one delta is not supported"
                    )
                    assert pm.tool_calls[0].function is not None, (
                        "Tool call without function is not supported"
                    )
                    parts.append(pm.tool_calls[0].function.arguments or "")

            tool_call_arguments = "".join(parts)
            if tool_call_arguments:
                yield _increment_sequence_number_and_return(
                    ResponseFunctionCallArgumentsDoneEvent(
                        type="response.function_call_arguments.done",
                        sequence_number=-1,
                        output_index=current_output_index,
                        item_id=current_item_id,
                        arguments=tool_call_arguments,
                        name=current_tool_call_name,
                    )
                )
                current_content_index = 0
                function_call_item = ResponseFunctionToolCall(
                    type="function_call",
                    name=current_tool_call_name,
                    arguments=tool_call_arguments,
                    status="completed",
                    id=current_item_id,
                    call_id=current_tool_call_id,
                )
                yield _increment_sequence_number_and_return(
                    ResponseOutputItemDoneEvent(
                        type="response.output_item.done",
                        sequence_number=-1,
                        output_index=current_output_index,
                        item=function_call_item,
                    )
                )

            elif previous_delta_messages[-1].reasoning is not None:
                reason_content = "".join(
                    pm.reasoning
                    for pm in previous_delta_messages
                    if pm.reasoning is not None
                )
                yield _increment_sequence_number_and_return(
                    ResponseReasoningTextDoneEvent(
                        type="response.reasoning_text.done",
                        item_id=current_item_id,
                        sequence_number=-1,
                        output_index=current_output_index,
                        content_index=current_content_index,
                        text=reason_content,
                    )
                )
                yield _increment_sequence_number_and_return(
                    ResponseReasoningPartDoneEvent(
                        type="response.reasoning_part.done",
                        sequence_number=-1,
                        item_id=current_item_id,
                        output_index=current_output_index,
                        content_index=current_content_index,
                        part=ResponseReasoningTextContent(
                            text=reason_content,
                            type="reasoning_text",
                        ),
                    )
                )
                reasoning_item = ResponseReasoningItem(
                    type="reasoning",
                    content=[
                        ResponseReasoningTextContent(
                            text=reason_content,
                            type="reasoning_text",
                        ),
                    ],
                    status="completed",
                    id=current_item_id,
                    summary=[],
                )
                yield _increment_sequence_number_and_return(
                    ResponseOutputItemDoneEvent(
                        type="response.output_item.done",
                        sequence_number=-1,
                        output_index=current_output_index,
                        item=reasoning_item,
                    )
                )
            elif previous_delta_messages[-1].content:
                final_content = "".join(
                    pm.content for pm in previous_delta_messages if pm.content
                )
                yield _increment_sequence_number_and_return(
                    ResponseTextDoneEvent(
                        type="response.output_text.done",
                        sequence_number=-1,
                        output_index=current_output_index,
                        content_index=current_content_index,
                        text=final_content,
                        logprobs=[],
                        item_id=current_item_id,
                    )
                )
                part = ResponseOutputText(
                    text=final_content,
                    type="output_text",
                    annotations=[],
                )
                yield _increment_sequence_number_and_return(
                    ResponseContentPartDoneEvent(
                        type="response.content_part.done",
                        sequence_number=-1,
                        item_id=current_item_id,
                        output_index=current_output_index,
                        content_index=current_content_index,
                        part=part,
                    )
                )
                item = ResponseOutputMessage(
                    type="message",
                    role="assistant",
                    content=[
                        part,
                    ],
                    status="completed",
                    id=current_item_id,
                    summary=[],
                )
                yield _increment_sequence_number_and_return(
                    ResponseOutputItemDoneEvent(
                        type="response.output_item.done",
                        sequence_number=-1,
                        output_index=current_output_index,
                        item=item,
                    )
                )