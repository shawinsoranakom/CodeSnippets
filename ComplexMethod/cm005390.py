async def sse_gen() -> AsyncGenerator[str, None]:
            try:
                yield self._build_chunk_sse(request_id, role="assistant", model=model_id)

                done = False
                while not done:
                    text = await queue.get()
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
                            sse_parts.append(f'data: {{"error": "{text.msg}"}}\n\n')
                            yield "".join(sse_parts)
                            return

                        sse_parts.append(self._build_chunk_sse(request_id, model=model_id, content=text))

                    if sse_parts:
                        yield "".join(sse_parts)

                # Tool calls are parsed after generation completes (not during streaming),
                # because the full token sequence is needed for reliable parsing.
                has_tool_calls = False
                if tool_config:
                    parsed = parse_tool_calls(processor, streamer.generated_token_ids, tool_config["schema"])
                    if parsed:
                        has_tool_calls = True
                        for i, tc in enumerate(parsed):
                            yield self._build_chunk_sse(
                                request_id,
                                model=model_id,
                                tool_calls=[
                                    ChoiceDeltaToolCall(
                                        index=i,
                                        type="function",
                                        id=f"{request_id}_tool_call_{i}",
                                        function={"name": tc["name"], "arguments": tc["arguments"]},
                                    )
                                ],
                            )

                hit_max = gen_config.max_new_tokens is not None and streamer.total_tokens >= gen_config.max_new_tokens
                if has_tool_calls:
                    finish_reason = "tool_calls"
                elif hit_max:
                    finish_reason = "length"
                else:
                    finish_reason = "stop"
                usage = CompletionUsage(
                    prompt_tokens=input_len,
                    completion_tokens=streamer.total_tokens,
                    total_tokens=input_len + streamer.total_tokens,
                )
                yield self._build_chunk_sse(
                    request_id,
                    finish_reason=finish_reason,
                    model=model_id,
                    usage=usage,
                )
            except (GeneratorExit, asyncio.CancelledError):
                # Client disconnected — abort generation to free GPU.
                # Re-raise is mandatory: Python raises RuntimeError if GeneratorExit is swallowed.
                streamer.cancel()
                raise