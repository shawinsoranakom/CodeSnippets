async def event_stream() -> AsyncGenerator[str, None]:
            nonlocal seq, output_index

            try:
                # 1. Created + In progress
                yield self.chunk_to_sse(
                    ResponseCreatedEvent(
                        type="response.created",
                        sequence_number=seq,
                        response=Response(**response_base, status="queued", output=[]),
                    )
                )
                seq += 1
                yield self.chunk_to_sse(
                    ResponseInProgressEvent(
                        type="response.in_progress",
                        sequence_number=seq,
                        response=Response(**response_base, status="in_progress", output=[]),
                    )
                )
                seq += 1

                # 2. Output item added (message)
                yield self.chunk_to_sse(
                    ResponseOutputItemAddedEvent(
                        type="response.output_item.added",
                        sequence_number=seq,
                        output_index=output_index,
                        item=ResponseOutputMessage(
                            id=msg_id,
                            type="message",
                            status="in_progress",
                            role="assistant",
                            content=[],
                        ),
                    )
                )
                seq += 1

                # 3. Content part added
                yield self.chunk_to_sse(
                    ResponseContentPartAddedEvent(
                        type="response.content_part.added",
                        item_id=msg_id,
                        sequence_number=seq,
                        output_index=output_index,
                        content_index=0,
                        part=ResponseOutputText(type="output_text", text="", annotations=[]),
                    )
                )
                seq += 1

                # 4. Stream tokens — drain queue to batch HTTP writes
                full_text = ""
                tool_calls = []
                done = False

                while not done:
                    text = await queue.get()
                    # Drain all available tokens for one batched HTTP write
                    batch = [text]
                    try:
                        while True:
                            batch.append(queue.get_nowait())
                    except asyncio.QueueEmpty:
                        pass

                    sse_parts: list[str] = []
                    for text in batch:
                        if text is None:
                            done = True
                            break
                        if isinstance(text, _StreamError):
                            logger.error(f"Exception in response generation: {text.msg}")
                            sse_parts.append(
                                self.chunk_to_sse(
                                    ResponseErrorEvent(type="error", sequence_number=seq, message=text.msg)
                                )
                            )
                            seq += 1
                            sse_parts.append(
                                self.chunk_to_sse(
                                    ResponseFailedEvent(
                                        type="response.failed",
                                        sequence_number=seq,
                                        response=Response(
                                            **response_base,
                                            status="failed",
                                            output=[],
                                            error=ResponseError(code="server_error", message=text.msg),
                                        ),
                                    )
                                )
                            )
                            yield "".join(sse_parts)
                            return

                        full_text += text
                        sse_parts.append(
                            self.chunk_to_sse(
                                ResponseTextDeltaEvent(
                                    type="response.output_text.delta",
                                    item_id=msg_id,
                                    sequence_number=seq,
                                    output_index=0,
                                    content_index=0,
                                    delta=text,
                                    logprobs=[],
                                )
                            )
                        )
                        seq += 1

                    if sse_parts:
                        yield "".join(sse_parts)

                # 5. Tool calls are parsed after generation completes (not during streaming),
                # because the full token sequence is needed for reliable parsing.
                if tool_config:
                    parsed = parse_tool_calls(processor, streamer.generated_token_ids, tool_config["schema"])
                    if parsed:
                        for i, tc in enumerate(parsed):
                            tc_id = f"{request_id}_tool_call_{i}"
                            tc_item = ResponseFunctionToolCall(
                                id=tc_id,
                                call_id=tc_id,
                                type="function_call",
                                name=tc["name"],
                                arguments=tc["arguments"],
                                status="completed",
                            )
                            tool_calls.append(tc_item)
                            output_index += 1
                            yield self.chunk_to_sse(
                                ResponseOutputItemAddedEvent(
                                    type="response.output_item.added",
                                    sequence_number=seq,
                                    output_index=output_index,
                                    item=tc_item,
                                )
                            )
                            seq += 1
                            yield self.chunk_to_sse(
                                ResponseFunctionCallArgumentsDoneEvent(
                                    type="response.function_call_arguments.done",
                                    sequence_number=seq,
                                    item_id=tc_id,
                                    output_index=output_index,
                                    arguments=tc["arguments"],
                                    name=tc["name"],
                                )
                            )
                            seq += 1
                            yield self.chunk_to_sse(
                                ResponseOutputItemDoneEvent(
                                    type="response.output_item.done",
                                    sequence_number=seq,
                                    output_index=output_index,
                                    item=tc_item,
                                )
                            )
                            seq += 1

                # 6. Close text output
                output_text_part = ResponseOutputText(type="output_text", text=full_text, annotations=[])
                yield self.chunk_to_sse(
                    ResponseTextDoneEvent(
                        type="response.output_text.done",
                        item_id=msg_id,
                        sequence_number=seq,
                        output_index=0,
                        content_index=0,
                        text=full_text,
                        logprobs=[],
                    )
                )
                seq += 1
                yield self.chunk_to_sse(
                    ResponseContentPartDoneEvent(
                        type="response.content_part.done",
                        item_id=msg_id,
                        sequence_number=seq,
                        output_index=0,
                        content_index=0,
                        part=output_text_part,
                    )
                )
                seq += 1

                msg_item = ResponseOutputMessage(
                    id=msg_id,
                    type="message",
                    status="completed",
                    role="assistant",
                    content=[output_text_part],
                    annotations=[],  # type: ignore[call-arg]
                )
                yield self.chunk_to_sse(
                    ResponseOutputItemDoneEvent(
                        type="response.output_item.done",
                        sequence_number=seq,
                        output_index=0,
                        item=msg_item,
                    )
                )
                seq += 1

                # 7. Completed
                all_output = [msg_item] + list(tool_calls)
                usage = compute_usage(input_len, streamer.total_tokens)
                yield self.chunk_to_sse(
                    ResponseCompletedEvent(
                        type="response.completed",
                        sequence_number=seq,
                        response=Response(**response_base, status="completed", output=all_output, usage=usage),
                    )
                )
                seq += 1
            except (GeneratorExit, asyncio.CancelledError):
                # Client disconnected — abort generation to free GPU.
                # Re-raise is mandatory: Python raises RuntimeError if GeneratorExit is swallowed.
                streamer.cancel()
                raise