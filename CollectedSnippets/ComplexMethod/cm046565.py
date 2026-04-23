async def gguf_tool_stream():
                try:
                    first_chunk = ChatCompletionChunk(
                        id = completion_id,
                        created = created,
                        model = model_name,
                        choices = [
                            ChunkChoice(
                                delta = ChoiceDelta(role = "assistant"),
                                finish_reason = None,
                            )
                        ],
                    )
                    yield f"data: {first_chunk.model_dump_json(exclude_none = True)}\n\n"

                    # Iterate the synchronous generator in a thread so
                    # the event loop stays free for disconnect detection.
                    gen = gguf_generate_with_tools()
                    prev_text = ""
                    _stream_usage = None
                    _stream_timings = None
                    while True:
                        if await request.is_disconnected():
                            cancel_event.set()
                            return

                        event = await asyncio.to_thread(next, gen, _tool_sentinel)
                        if event is _tool_sentinel:
                            break

                        if event["type"] == "status":
                            # Empty status marks an iteration boundary
                            # in the GGUF tool loop (e.g. after a
                            # re-prompt).  Reset the cumulative cursor
                            # so the next assistant turn streams cleanly.
                            if not event["text"]:
                                prev_text = ""
                            # Emit tool status as a custom SSE event
                            # (including empty ones to clear UI badges)
                            status_data = json.dumps(
                                {
                                    "type": "tool_status",
                                    "content": event["text"],
                                }
                            )
                            yield f"data: {status_data}\n\n"
                            continue

                        if event["type"] in ("tool_start", "tool_end"):
                            if event["type"] == "tool_start":
                                prev_text = ""
                            yield f"data: {json.dumps(event)}\n\n"
                            continue

                        if event["type"] == "metadata":
                            _stream_usage = event.get("usage")
                            _stream_timings = event.get("timings")
                            continue

                        # "content" type -- cumulative text
                        # Sanitize the full cumulative then diff against
                        # the last sanitized snapshot so cross-chunk XML
                        # tags are handled correctly.
                        raw_cumulative = event.get("text", "")
                        clean_cumulative = _TOOL_XML_RE.sub("", raw_cumulative)
                        new_text = clean_cumulative[len(prev_text) :]
                        prev_text = clean_cumulative
                        if not new_text:
                            continue
                        chunk = ChatCompletionChunk(
                            id = completion_id,
                            created = created,
                            model = model_name,
                            choices = [
                                ChunkChoice(
                                    delta = ChoiceDelta(content = new_text),
                                    finish_reason = None,
                                )
                            ],
                        )
                        yield f"data: {chunk.model_dump_json(exclude_none = True)}\n\n"

                    final_chunk = ChatCompletionChunk(
                        id = completion_id,
                        created = created,
                        model = model_name,
                        choices = [
                            ChunkChoice(
                                delta = ChoiceDelta(),
                                finish_reason = "stop",
                            )
                        ],
                    )
                    yield f"data: {final_chunk.model_dump_json(exclude_none = True)}\n\n"
                    # Usage chunk (OpenAI-standard: choices=[], usage populated)
                    if _stream_usage or _stream_timings:
                        usage_obj = CompletionUsage(
                            prompt_tokens = (_stream_usage or {}).get("prompt_tokens", 0),
                            completion_tokens = (_stream_usage or {}).get(
                                "completion_tokens", 0
                            ),
                            total_tokens = (_stream_usage or {}).get("total_tokens", 0),
                        )
                        usage_chunk = ChatCompletionChunk(
                            id = completion_id,
                            created = created,
                            model = model_name,
                            choices = [],
                            usage = usage_obj,
                            timings = _stream_timings,
                        )
                        yield f"data: {usage_chunk.model_dump_json(exclude_none = True)}\n\n"
                    yield "data: [DONE]\n\n"

                except asyncio.CancelledError:
                    cancel_event.set()
                    raise
                except Exception as e:
                    import traceback

                    tb = traceback.format_exc()
                    logger.error(f"Error during GGUF tool streaming: {e}\n{tb}")
                    error_chunk = {
                        "error": {
                            "message": _friendly_error(e),
                            "type": "server_error",
                        },
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"