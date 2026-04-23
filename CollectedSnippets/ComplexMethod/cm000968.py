async def _baseline_llm_caller(
    messages: list[dict[str, Any]],
    tools: Sequence[Any],
    *,
    state: _BaselineStreamState,
) -> LLMLoopResponse:
    """Stream an OpenAI-compatible response and collect results.

    Extracted from ``stream_chat_completion_baseline`` for readability.
    """
    _emit(state, StreamStartStep())
    # Fresh thinking-strip state per round so a malformed unclosed
    # block in one LLM call cannot silently drop content in the next.
    state.thinking_stripper = _ThinkingStripper()

    round_text = ""
    try:
        client = _get_openai_client()
        # Cache markers are accepted by Anthropic AND Moonshot (via OR's
        # Anthropic-compat endpoint).  OpenAI/Grok/Gemini 400 on the
        # unknown ``cache_control`` field — tools were precomputed in
        # stream_chat_completion_baseline via _mark_tools_with_cache_control
        # with the same gate, so on unsupported routes tools ship
        # unmarked too.
        #
        # The ``anthropic-beta`` header is only emitted for genuinely
        # Anthropic routes (see :func:`_is_anthropic_model`) — Moonshot
        # doesn't need the beta header; sending it is a no-op but we
        # keep the check strict for clarity.
        #
        # `extra_body` `usage.include=true` asks OpenRouter to embed the
        # real generation cost into the final usage chunk — required by
        # the cost-based rate limiter in routes.py.  Separate from the
        # caching headers, always sent.
        supports_cache = _supports_prompt_cache_markers(state.model)
        if supports_cache:
            # Build the cached system dict once per session and splice it in
            # on each round.  The full ``messages`` list grows with every
            # tool call, so copying the entire list just to mutate index 0
            # scales with conversation length (sentry flagged this); this
            # splice touches only list slots, not message contents.
            if (
                state.cached_system_message is None
                and messages
                and messages[0].get("role") == "system"
            ):
                state.cached_system_message = _build_cached_system_message(messages[0])
            if state.cached_system_message is not None and messages:
                final_messages = [state.cached_system_message, *messages[1:]]
            else:
                final_messages = messages
            extra_headers = (
                _fresh_anthropic_caching_headers()
                if _is_anthropic_model(state.model)
                else None
            )
        else:
            final_messages = messages
            extra_headers = None
        typed_messages = cast(list[ChatCompletionMessageParam], final_messages)
        extra_body: dict[str, Any] = dict(_OPENROUTER_INCLUDE_USAGE_COST)
        reasoning_param = reasoning_extra_body(
            state.model, config.claude_agent_max_thinking_tokens
        )
        if reasoning_param:
            extra_body.update(reasoning_param)
        create_kwargs: dict[str, Any] = {
            "model": state.model,
            "messages": typed_messages,
            "stream": True,
            "stream_options": {"include_usage": True},
            "extra_body": extra_body,
        }
        if extra_headers:
            create_kwargs["extra_headers"] = extra_headers
        if tools:
            create_kwargs["tools"] = cast(list[ChatCompletionToolParam], list(tools))
        response = await client.chat.completions.create(**create_kwargs)
        tool_calls_by_index: dict[int, dict[str, str]] = {}

        # Iterate under an inner try/finally so early exits (cancel, tool-call
        # break, exception) always release the underlying httpx connection.
        # Without this, openai.AsyncStream leaks the streaming response and
        # the TCP socket ends up in CLOSE_WAIT until the process exits.
        try:
            async for chunk in response:
                if chunk.usage:
                    state.turn_prompt_tokens += chunk.usage.prompt_tokens or 0
                    state.turn_completion_tokens += chunk.usage.completion_tokens or 0
                    ptd = chunk.usage.prompt_tokens_details
                    if ptd:
                        state.turn_cache_read_tokens += ptd.cached_tokens or 0
                        state.turn_cache_creation_tokens += (
                            _extract_cache_creation_tokens(ptd)
                        )
                    cost = _extract_usage_cost(chunk.usage)
                    if cost is not None:
                        state.cost_usd = (state.cost_usd or 0.0) + cost
                    elif (
                        "cost" not in (chunk.usage.model_extra or {})
                        and not state.cost_missing_logged
                    ):
                        # Field absent (non-OpenRouter route, or OpenRouter
                        # misconfigured) — warn once per stream so error
                        # monitoring picks up persistent misses without
                        # flooding. Invalid values already logged inside
                        # _extract_usage_cost, so no duplicate warning here.
                        logger.warning(
                            "[Baseline] usage chunk missing cost (model=%s, "
                            "prompt=%s, completion=%s) — rate-limit will "
                            "skip this call",
                            state.model,
                            chunk.usage.prompt_tokens,
                            chunk.usage.completion_tokens,
                        )
                        state.cost_missing_logged = True

                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                _emit_all(state, state.reasoning_emitter.on_delta(delta))

                if delta.content:
                    # Text and reasoning must not interleave on the wire — the
                    # AI SDK maps distinct start/end pairs to distinct UI
                    # parts.  Close any open reasoning block before emitting
                    # the first text delta of this run.
                    _emit_all(state, state.reasoning_emitter.close())
                    emit = state.thinking_stripper.process(delta.content)
                    if emit:
                        if not state.text_started:
                            _emit(state, StreamTextStart(id=state.text_block_id))
                            state.text_started = True
                        round_text += emit
                        _emit(
                            state,
                            StreamTextDelta(id=state.text_block_id, delta=emit),
                        )

                if delta.tool_calls:
                    # Same rule as the text branch: close any open reasoning
                    # block before a tool_use starts so the AI SDK treats
                    # reasoning and tool-use as distinct parts.
                    _emit_all(state, state.reasoning_emitter.close())
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_by_index:
                            tool_calls_by_index[idx] = {
                                "id": "",
                                "name": "",
                                "arguments": "",
                            }
                        entry = tool_calls_by_index[idx]
                        if tc.id:
                            entry["id"] = tc.id
                        if tc.function and tc.function.name:
                            entry["name"] = tc.function.name
                        if tc.function and tc.function.arguments:
                            entry["arguments"] += tc.function.arguments
        finally:
            # Release the streaming httpx connection back to the pool on every
            # exit path (normal completion, break, exception). openai.AsyncStream
            # does not auto-close when the async-for loop exits early.
            try:
                await response.close()
            except Exception:
                pass

    finally:
        # Close open blocks on both normal and exception paths so the
        # frontend always sees matched start/end pairs.  An exception mid
        # ``async for chunk in response`` would otherwise leave reasoning
        # and/or text unterminated and only ``StreamFinishStep`` emitted —
        # the Reasoning / Text collapses would never finalise.
        _emit_all(state, state.reasoning_emitter.close())
        # Flush any buffered text held back by the thinking stripper.
        tail = state.thinking_stripper.flush()
        if tail:
            if not state.text_started:
                _emit(state, StreamTextStart(id=state.text_block_id))
                state.text_started = True
            round_text += tail
            _emit(state, StreamTextDelta(id=state.text_block_id, delta=tail))
        if state.text_started:
            _emit(state, StreamTextEnd(id=state.text_block_id))
            state.text_started = False
            state.text_block_id = str(uuid.uuid4())
        # Always persist partial text so the session history stays consistent,
        # even when the stream is interrupted by an exception.
        state.assistant_text += round_text
        # Always emit StreamFinishStep to match the StreamStartStep,
        # even if an exception occurred during streaming.
        _emit(state, StreamFinishStep())

    # Convert to shared format
    llm_tool_calls = [
        LLMToolCall(
            id=tc["id"],
            name=tc["name"],
            arguments=tc["arguments"] or "{}",
        )
        for tc in tool_calls_by_index.values()
    ]

    return LLMLoopResponse(
        response_text=round_text or None,
        tool_calls=llm_tool_calls,
        raw_response=None,  # Not needed for baseline conversation updater
        prompt_tokens=0,  # Tracked via state accumulators
        completion_tokens=0,
    )