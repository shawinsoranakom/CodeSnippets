async def anthropic_messages(
    payload: AnthropicMessagesRequest,
    request: Request,
    current_subject: str = Depends(get_current_subject),
):
    """
    Anthropic-compatible Messages API endpoint.

    Translates Anthropic message format to internal OpenAI format, runs
    through the existing agentic tool loop when tools are provided, and
    returns responses in Anthropic Messages API format (streaming SSE or
    non-streaming JSON).
    """
    llama_backend = get_llama_cpp_backend()
    if not llama_backend.is_loaded:
        raise HTTPException(
            status_code = 503,
            detail = "No GGUF model loaded. Load a GGUF model first.",
        )

    model_name = getattr(llama_backend, "model_identifier", None) or payload.model
    message_id = f"msg_{uuid.uuid4().hex[:24]}"

    # ── Translate Anthropic → OpenAI ──────────────────────────
    openai_messages = anthropic_messages_to_openai(
        [m.model_dump() for m in payload.messages],
        payload.system,
    )

    # Enforce vision guard + re-encode embedded images to PNG so the
    # Anthropic endpoint matches the behavior of /v1/chat/completions.
    _has_image = _normalize_anthropic_openai_images(
        openai_messages, llama_backend.is_vision
    )

    temperature = payload.temperature if payload.temperature is not None else 0.6
    top_p = payload.top_p if payload.top_p is not None else 0.95
    top_k = payload.top_k if payload.top_k is not None else 20
    min_p = payload.min_p if payload.min_p is not None else 0.01
    repetition_penalty = (
        payload.repetition_penalty if payload.repetition_penalty is not None else 1.0
    )
    presence_penalty = (
        payload.presence_penalty if payload.presence_penalty is not None else 0.0
    )
    stop = payload.stop_sequences or None

    # Translate Anthropic tool_choice to OpenAI format for forwarding to
    # llama-server. Falls back to "auto" when unset or unrecognized, which
    # matches the prior hardcoded behavior.
    openai_tool_choice = anthropic_tool_choice_to_openai(payload.tool_choice)
    if openai_tool_choice is None:
        openai_tool_choice = "auto"

    cancel_event = threading.Event()

    # ── Tool routing ──────────────────────────────────────────
    # Three paths:
    # 1. enable_tools=true → server-side execution of built-in tools (Unsloth shorthand)
    # 2. tools=[...] only  → client-side pass-through (standard Anthropic behavior)
    # 3. neither           → plain chat
    # Server-side agentic loop doesn't support multimodal input — matches
    # the `not image_b64` gate in /v1/chat/completions.
    server_tools = (
        payload.enable_tools and llama_backend.supports_tools and not _has_image
    )
    client_tools = (
        not server_tools
        and payload.tools
        and len(payload.tools) > 0
        and llama_backend.supports_tools
    )

    # ── Client-side pass-through path ─────────────────────────
    if client_tools:
        openai_tools = anthropic_tools_to_openai(payload.tools)

        if payload.stream:
            return await _anthropic_passthrough_stream(
                request,
                cancel_event,
                llama_backend,
                openai_messages,
                openai_tools,
                temperature,
                top_p,
                top_k,
                payload.max_tokens,
                message_id,
                model_name,
                stop = stop,
                min_p = min_p,
                repetition_penalty = repetition_penalty,
                presence_penalty = presence_penalty,
                tool_choice = openai_tool_choice,
            )
        return await _anthropic_passthrough_non_streaming(
            llama_backend,
            openai_messages,
            openai_tools,
            temperature,
            top_p,
            top_k,
            payload.max_tokens,
            message_id,
            model_name,
            stop = stop,
            min_p = min_p,
            repetition_penalty = repetition_penalty,
            presence_penalty = presence_penalty,
            tool_choice = openai_tool_choice,
        )

    if server_tools:
        from core.inference.tools import ALL_TOOLS

        if payload.enabled_tools is not None:
            openai_tools = [
                t for t in ALL_TOOLS if t["function"]["name"] in payload.enabled_tools
            ]
        else:
            openai_tools = ALL_TOOLS

        # Build tool-use system prompt nudge (same logic as /chat/completions)
        _tool_names = {t["function"]["name"] for t in openai_tools}
        _has_web = "web_search" in _tool_names
        _has_code = "python" in _tool_names or "terminal" in _tool_names

        _date_line = f"The current date is {_date.today().isoformat()}."
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
            # Inject into system prompt
            if openai_messages and openai_messages[0].get("role") == "system":
                openai_messages[0]["content"] = (
                    openai_messages[0]["content"].rstrip() + "\n\n" + _nudge
                )
            else:
                openai_messages.insert(0, {"role": "system", "content": _nudge})

        # Strip stale tool-call XML from conversation
        for _msg in openai_messages:
            if _msg.get("role") == "assistant" and isinstance(_msg.get("content"), str):
                _msg["content"] = _TOOL_XML_RE.sub("", _msg["content"]).strip()

        def _run_tool_gen():
            return llama_backend.generate_chat_completion_with_tools(
                messages = openai_messages,
                tools = openai_tools,
                temperature = temperature,
                top_p = top_p,
                top_k = top_k,
                min_p = min_p,
                repetition_penalty = repetition_penalty,
                presence_penalty = presence_penalty,
                max_tokens = payload.max_tokens,
                stop = stop,
                cancel_event = cancel_event,
                max_tool_iterations = 25,
                auto_heal_tool_calls = True,
                tool_call_timeout = 300,
                session_id = payload.session_id,
            )

        if payload.stream:
            return await _anthropic_tool_stream(
                request,
                cancel_event,
                _run_tool_gen,
                message_id,
                model_name,
            )
        return await _anthropic_tool_non_streaming(
            _run_tool_gen,
            message_id,
            model_name,
        )

    # ── No-tool path ──────────────────────────────────────────
    def _run_plain_gen():
        return llama_backend.generate_chat_completion(
            messages = openai_messages,
            temperature = temperature,
            top_p = top_p,
            top_k = top_k,
            min_p = min_p,
            repetition_penalty = repetition_penalty,
            presence_penalty = presence_penalty,
            max_tokens = payload.max_tokens,
            stop = stop,
            cancel_event = cancel_event,
        )

    if payload.stream:
        return await _anthropic_plain_stream(
            request,
            cancel_event,
            _run_plain_gen,
            message_id,
            model_name,
        )
    return await _anthropic_plain_non_streaming(
        _run_plain_gen,
        message_id,
        model_name,
    )