async def openai_chat_completions(
    payload: ChatCompletionRequest,
    request: Request,
    current_subject: str = Depends(get_current_subject),
):
    """
    OpenAI-compatible chat completions endpoint.

    Supports multimodal messages: ``content`` may be a plain string or a
    list of content parts (``text`` / ``image_url``).

    Streaming (default):  returns SSE chunks matching OpenAI's format.
    Non-streaming:        returns a single ChatCompletion JSON object.

    Automatically routes to the correct backend:
    - GGUF models → llama-server via LlamaCppBackend
    - Other models → Unsloth/transformers via InferenceBackend
    """
    llama_backend = get_llama_cpp_backend()
    using_gguf = llama_backend.is_loaded

    # ── Determine which backend is active ─────────────────────
    if using_gguf:
        model_name = llama_backend.model_identifier or payload.model
        if getattr(llama_backend, "_is_audio", False):
            return await generate_audio(payload, request)
    else:
        backend = get_inference_backend()
        if not backend.active_model_name:
            raise HTTPException(
                status_code = 400,
                detail = "No model loaded. Call POST /inference/load first.",
            )
        model_name = backend.active_model_name or payload.model

        # ── Audio TTS path: auto-route to audio generation ────
        # (Whisper is ASR not TTS — handled below in audio input path)
        model_info = backend.models.get(backend.active_model_name, {})
        if model_info.get("is_audio") and model_info.get("audio_type") != "whisper":
            return await generate_audio(payload, request)

        # ── Whisper without audio: return clear error ──
        if model_info.get("audio_type") == "whisper" and not payload.audio_base64:
            raise HTTPException(
                status_code = 400,
                detail = "Whisper models require audio input. Please upload an audio file.",
            )

        # ── Audio INPUT path: decode WAV and route to audio input generation ──
        if payload.audio_base64 and model_info.get("has_audio_input"):
            audio_array = _decode_audio_base64(payload.audio_base64)
            system_prompt, chat_messages, _ = _extract_content_parts(payload.messages)
            cancel_event = threading.Event()
            completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
            created = int(time.time())

            def audio_input_generate():
                if model_info.get("audio_type") == "whisper":
                    return backend.generate_whisper_response(
                        audio_array = audio_array,
                        cancel_event = cancel_event,
                    )
                return backend.generate_audio_input_response(
                    messages = chat_messages,
                    system_prompt = system_prompt,
                    audio_array = audio_array,
                    temperature = payload.temperature,
                    top_p = payload.top_p,
                    top_k = payload.top_k,
                    min_p = payload.min_p,
                    max_new_tokens = payload.max_tokens or 2048,
                    repetition_penalty = payload.repetition_penalty,
                    cancel_event = cancel_event,
                )

            if payload.stream:

                async def audio_input_stream():
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

                        for chunk_text in audio_input_generate():
                            if await request.is_disconnected():
                                cancel_event.set()
                                return
                            if chunk_text:
                                chunk = ChatCompletionChunk(
                                    id = completion_id,
                                    created = created,
                                    model = model_name,
                                    choices = [
                                        ChunkChoice(
                                            delta = ChoiceDelta(content = chunk_text),
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
                                ChunkChoice(delta = ChoiceDelta(), finish_reason = "stop")
                            ],
                        )
                        yield f"data: {final_chunk.model_dump_json(exclude_none = True)}\n\n"
                        yield "data: [DONE]\n\n"
                    except asyncio.CancelledError:
                        cancel_event.set()
                        raise
                    except Exception as e:
                        logger.error(
                            f"Error during audio input streaming: {e}", exc_info = True
                        )
                        yield f"data: {json.dumps({'error': {'message': _friendly_error(e), 'type': 'server_error'}})}\n\n"

                return StreamingResponse(
                    audio_input_stream(),
                    media_type = "text/event-stream",
                    headers = {
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )
            else:
                full_text = "".join(audio_input_generate())
                response = ChatCompletion(
                    id = completion_id,
                    created = created,
                    model = model_name,
                    choices = [
                        CompletionChoice(
                            message = CompletionMessage(content = full_text),
                            finish_reason = "stop",
                        )
                    ],
                )
                return JSONResponse(content = response.model_dump())

    # ── Standard OpenAI function-calling pass-through (GGUF only) ────
    # When a client (opencode / Claude Code via OpenAI compat / Cursor /
    # Continue / ...) sends standard OpenAI `tools` without Studio's
    # `enable_tools` shorthand, forward the request to llama-server
    # verbatim so structured `tool_calls` flow back to the client. This
    # branch runs BEFORE `_extract_content_parts` because that helper is
    # unaware of `role="tool"` messages and assistant messages that only
    # carry `tool_calls` (content=None) — both of which are valid in
    # multi-turn client-side tool loops.
    _has_tool_messages = any(m.role == "tool" or m.tool_calls for m in payload.messages)
    if (
        using_gguf
        and llama_backend.supports_tools
        and not payload.enable_tools
        and ((payload.tools and len(payload.tools) > 0) or _has_tool_messages)
    ):
        # Preserve the vision guard that would otherwise run in the
        # non-passthrough path below: text-only tool-capable GGUFs
        # should return a clear 400 here rather than forwarding the
        # image to llama-server and surfacing an opaque upstream error.
        if not llama_backend.is_vision and (
            payload.image_base64
            or any(
                isinstance(m.content, list)
                and any(isinstance(p, ImageContentPart) for p in m.content)
                for m in payload.messages
            )
        ):
            raise HTTPException(
                status_code = 400,
                detail = "Image provided but current GGUF model does not support vision.",
            )

        cancel_event = threading.Event()
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        if payload.stream:
            return await _openai_passthrough_stream(
                request,
                cancel_event,
                llama_backend,
                payload,
                model_name,
                completion_id,
            )
        return await _openai_passthrough_non_streaming(
            llama_backend,
            payload,
            model_name,
        )

    # ── Parse messages (handles multimodal content parts) ─────
    system_prompt, chat_messages, extracted_image_b64 = _extract_content_parts(
        payload.messages
    )

    if not chat_messages:
        raise HTTPException(
            status_code = 400,
            detail = "At least one non-system message is required.",
        )

    # ── GGUF path: proxy to llama-server /v1/chat/completions ──
    if using_gguf:
        # Reject images if this GGUF model doesn't support vision
        image_b64 = extracted_image_b64 or payload.image_base64
        if image_b64 and not llama_backend.is_vision:
            raise HTTPException(
                status_code = 400,
                detail = "Image provided but current GGUF model does not support vision.",
            )

        # Convert image to PNG for llama-server (stb_image has limited format support)
        if image_b64:
            try:
                import base64 as _b64
                from io import BytesIO as _BytesIO
                from PIL import Image as _Image

                raw = _b64.b64decode(image_b64)
                # Normalize to RGB so PNG encoding succeeds regardless of
                # source mode (RGBA, P, L, CMYK, I, F, ...). Previously
                # we only converted RGBA, which left CMYK/I/F to raise at
                # img.save(PNG).
                img = _Image.open(_BytesIO(raw)).convert("RGB")
                buf = _BytesIO()
                img.save(buf, format = "PNG")
                image_b64 = _b64.b64encode(buf.getvalue()).decode("ascii")
            except Exception as e:
                raise HTTPException(
                    status_code = 400, detail = f"Failed to process image: {e}"
                )

        # Build message list with system prompt prepended
        gguf_messages = []
        if system_prompt:
            gguf_messages.append({"role": "system", "content": system_prompt})
        gguf_messages.extend(chat_messages)

        cancel_event = threading.Event()

        completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())

        # ── Tool-calling path (agentic loop) ──────────────────
        use_tools = (
            payload.enable_tools and llama_backend.supports_tools and not image_b64
        )

        if use_tools:
            from core.inference.tools import ALL_TOOLS

            if payload.enabled_tools is not None:
                tools_to_use = [
                    t
                    for t in ALL_TOOLS
                    if t["function"]["name"] in payload.enabled_tools
                ]
            else:
                tools_to_use = ALL_TOOLS

            # ── Tool-use system prompt nudge ──────────────────────
            _tool_names = {t["function"]["name"] for t in tools_to_use}
            _has_web = "web_search" in _tool_names
            _has_code = "python" in _tool_names or "terminal" in _tool_names

            _date_line = f"The current date is {_date.today().isoformat()}."

            # Small models (<9B) struggle with multi-step search plans,
            # so simplify the web tips to avoid plan-then-stall behavior.
            _model_size_b = _extract_model_size_b(model_name)
            _is_small_model = _model_size_b is not None and _model_size_b < 9

            if _is_small_model:
                _web_tips = "Do not repeat the same search query."
            else:
                _web_tips = (
                    "When you search and find a relevant URL in the results, "
                    "fetch its full content by calling web_search with the url parameter. "
                    "Do not repeat the same search query. If a search returns "
                    "no useful results, try rephrasing or fetching a result URL directly."
                )
            _code_tips = (
                "Use code execution for math, calculations, data processing, "
                "or to parse and analyze information from tool results."
            )

            if _has_web and _has_code:
                _nudge = (
                    _date_line + " "
                    "You have access to tools. When appropriate, prefer using "
                    "tools rather than answering from memory. "
                    + _web_tips
                    + " "
                    + _code_tips
                )
            elif _has_code:
                _nudge = (
                    _date_line + " "
                    "You have access to tools. When appropriate, prefer using "
                    "code execution rather than answering from memory. " + _code_tips
                )
            elif _has_web:
                _nudge = (
                    _date_line + " "
                    "You have access to tools. When appropriate, prefer using "
                    "web search for up-to-date or uncertain factual "
                    "information rather than answering from memory. " + _web_tips
                )
            else:
                _nudge = ""

            if _nudge:
                _nudge += _TOOL_ACTION_NUDGE
                # Append nudge to system prompt (preserve user's prompt)
                if system_prompt:
                    system_prompt = system_prompt.rstrip() + "\n\n" + _nudge
                else:
                    system_prompt = _nudge
                # Rebuild gguf_messages with updated system prompt
                gguf_messages = []
                if system_prompt:
                    gguf_messages.append({"role": "system", "content": system_prompt})
                gguf_messages.extend(chat_messages)

            # ── Strip stale tool-call XML from conversation history ─
            for _msg in gguf_messages:
                if _msg.get("role") == "assistant" and isinstance(
                    _msg.get("content"), str
                ):
                    _msg["content"] = _TOOL_XML_RE.sub("", _msg["content"]).strip()

            def gguf_generate_with_tools():
                return llama_backend.generate_chat_completion_with_tools(
                    messages = gguf_messages,
                    tools = tools_to_use,
                    temperature = payload.temperature,
                    top_p = payload.top_p,
                    top_k = payload.top_k,
                    min_p = payload.min_p,
                    max_tokens = payload.max_tokens,
                    repetition_penalty = payload.repetition_penalty,
                    presence_penalty = payload.presence_penalty,
                    cancel_event = cancel_event,
                    enable_thinking = payload.enable_thinking,
                    auto_heal_tool_calls = payload.auto_heal_tool_calls
                    if payload.auto_heal_tool_calls is not None
                    else True,
                    max_tool_iterations = payload.max_tool_calls_per_message
                    if payload.max_tool_calls_per_message is not None
                    else 25,
                    tool_call_timeout = payload.tool_call_timeout
                    if payload.tool_call_timeout is not None
                    else 300,
                    session_id = payload.session_id,
                )

            _tool_sentinel = object()

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

            return StreamingResponse(
                gguf_tool_stream(),
                media_type = "text/event-stream",
                headers = {
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        # ── Standard GGUF path (no tools) ─────────────────────

        def gguf_generate():
            return llama_backend.generate_chat_completion(
                messages = gguf_messages,
                image_b64 = image_b64,
                temperature = payload.temperature,
                top_p = payload.top_p,
                top_k = payload.top_k,
                min_p = payload.min_p,
                max_tokens = payload.max_tokens,
                repetition_penalty = payload.repetition_penalty,
                presence_penalty = payload.presence_penalty,
                cancel_event = cancel_event,
                enable_thinking = payload.enable_thinking,
            )

        _gguf_sentinel = object()

        if payload.stream:

            async def gguf_stream_chunks():
                try:
                    # First chunk: role
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
                    gen = gguf_generate()
                    prev_text = ""
                    _stream_usage = None
                    _stream_timings = None
                    while True:
                        if await request.is_disconnected():
                            cancel_event.set()
                            return
                        cumulative = await asyncio.to_thread(next, gen, _gguf_sentinel)
                        if cumulative is _gguf_sentinel:
                            break
                        # Capture server metadata for final usage chunk
                        if isinstance(cumulative, dict):
                            if cumulative.get("type") == "metadata":
                                _stream_usage = cumulative.get("usage")
                                _stream_timings = cumulative.get("timings")
                            else:
                                logger.warning(
                                    "gguf_stream_chunks: unexpected dict event: %s",
                                    {
                                        k: v
                                        for k, v in cumulative.items()
                                        if k != "timings"
                                    },
                                )
                            continue
                        new_text = cumulative[len(prev_text) :]
                        prev_text = cumulative
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

                    # Final chunk
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
                    logger.error(f"Error during GGUF streaming: {e}", exc_info = True)
                    error_chunk = {
                        "error": {
                            "message": _friendly_error(e),
                            "type": "server_error",
                        },
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"

            return StreamingResponse(
                gguf_stream_chunks(),
                media_type = "text/event-stream",
                headers = {
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            try:
                full_text = ""
                for token in gguf_generate():
                    if isinstance(token, dict):
                        continue  # skip metadata dict in non-streaming path
                    full_text = token

                response = ChatCompletion(
                    id = completion_id,
                    created = created,
                    model = model_name,
                    choices = [
                        CompletionChoice(
                            message = CompletionMessage(content = full_text),
                            finish_reason = "stop",
                        )
                    ],
                )
                return JSONResponse(content = response.model_dump())

            except Exception as e:
                logger.error(f"Error during GGUF completion: {e}", exc_info = True)
                raise HTTPException(status_code = 500, detail = str(e))

    # ── Standard Unsloth path ─────────────────────────────────

    # Decode image (from content parts OR legacy field)
    image_b64 = extracted_image_b64 or payload.image_base64
    image = None

    if image_b64:
        try:
            import base64
            from PIL import Image
            from io import BytesIO

            model_info = backend.models.get(backend.active_model_name, {})
            if not model_info.get("is_vision"):
                raise HTTPException(
                    status_code = 400,
                    detail = "Image provided but current model is text-only. Load a vision model.",
                )

            image_data = base64.b64decode(image_b64)
            image = Image.open(BytesIO(image_data))
            image = backend.resize_image(image)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code = 400, detail = f"Failed to decode image: {e}")

    # Shared generation kwargs
    gen_kwargs = dict(
        messages = chat_messages,
        system_prompt = system_prompt,
        image = image,
        temperature = payload.temperature,
        top_p = payload.top_p,
        top_k = payload.top_k,
        min_p = payload.min_p,
        max_new_tokens = payload.max_tokens or 2048,
        repetition_penalty = payload.repetition_penalty,
    )

    # Choose generation path (adapter-controlled or standard)
    cancel_event = threading.Event()

    if payload.use_adapter is not None:

        def generate():
            return backend.generate_with_adapter_control(
                use_adapter = payload.use_adapter,
                cancel_event = cancel_event,
                **gen_kwargs,
            )
    else:

        def generate():
            return backend.generate_chat_response(
                cancel_event = cancel_event, **gen_kwargs
            )

    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    # ── Streaming response ────────────────────────────────────────
    if payload.stream:

        async def stream_chunks():
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

                prev_text = ""
                # Run sync generator in thread pool to avoid blocking
                # the event loop. Critical for compare mode: two SSE
                # requests arrive concurrently but the orchestrator
                # serializes them via _gen_lock. Without run_in_executor
                # the second request's blocking lock acquisition would
                # freeze the entire event loop, stalling both streams.
                _DONE = object()  # sentinel for generator exhaustion
                loop = asyncio.get_event_loop()
                gen = generate()
                while True:
                    # next(gen, _DONE) returns _DONE instead of raising
                    # StopIteration — StopIteration cannot propagate
                    # through asyncio futures (Python limitation).
                    cumulative = await loop.run_in_executor(None, next, gen, _DONE)
                    if cumulative is _DONE:
                        break
                    if await request.is_disconnected():
                        cancel_event.set()
                        backend.reset_generation_state()
                        return
                    new_text = cumulative[len(prev_text) :]
                    prev_text = cumulative
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
                yield "data: [DONE]\n\n"

            except asyncio.CancelledError:
                cancel_event.set()
                backend.reset_generation_state()
                raise
            except Exception as e:
                backend.reset_generation_state()
                logger.error(f"Error during OpenAI streaming: {e}", exc_info = True)
                error_chunk = {
                    "error": {
                        "message": _friendly_error(e),
                        "type": "server_error",
                    },
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"

        return StreamingResponse(
            stream_chunks(),
            media_type = "text/event-stream",
            headers = {
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # ── Non-streaming response ────────────────────────────────────
    else:
        try:
            full_text = ""
            for token in generate():
                full_text = token

            response = ChatCompletion(
                id = completion_id,
                created = created,
                model = model_name,
                choices = [
                    CompletionChoice(
                        message = CompletionMessage(content = full_text),
                        finish_reason = "stop",
                    )
                ],
            )
            return JSONResponse(content = response.model_dump())

        except Exception as e:
            backend.reset_generation_state()
            logger.error(f"Error during OpenAI completion: {e}", exc_info = True)
            raise HTTPException(status_code = 500, detail = str(e))