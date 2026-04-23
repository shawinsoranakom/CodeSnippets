async def stream_chat_completion_baseline(
    session_id: str,
    message: str | None = None,
    is_user_message: bool = True,
    user_id: str | None = None,
    session: ChatSession | None = None,
    file_ids: list[str] | None = None,
    permissions: "CopilotPermissions | None" = None,
    context: dict[str, str] | None = None,
    mode: CopilotMode | None = None,
    model: CopilotLlmModel | None = None,
    request_arrival_at: float = 0.0,
    **_kwargs: Any,
) -> AsyncGenerator[StreamBaseResponse, None]:
    """Baseline LLM with tool calling via OpenAI-compatible API.

    Designed as a fallback when the Claude Agent SDK is unavailable.
    Uses the same tool registry as the SDK path but routes through any
    OpenAI-compatible provider (e.g. OpenRouter).

    Flow: stream response -> if tool_calls, execute them -> feed results back -> repeat.
    """
    if session is None:
        session = await get_chat_session(session_id, user_id)

    if not session:
        raise NotFoundError(
            f"Session {session_id} not found. Please create a new session first."
        )

    # Drop orphan tool_use + trailing stop-marker rows left by a previous
    # Stop mid-tool-call so the new turn starts from a well-formed message list.
    prune_orphan_tool_calls(
        session.messages, log_prefix=f"[Baseline] [{session_id[:12]}]"
    )

    # Strip any user-injected <user_context> tags on every turn.
    # Only the server-injected prefix on the first message is trusted.
    if message:
        message = strip_user_context_tags(message)

    if maybe_append_user_message(session, message, is_user_message):
        if is_user_message:
            track_user_message(
                user_id=user_id,
                session_id=session_id,
                message_length=len(message or ""),
            )

    # Capture count *before* the pending drain so is_first_turn and the
    # transcript staleness check are not skewed by queued messages.
    _pre_drain_msg_count = len(session.messages)

    # Drain any messages the user queued via POST /messages/pending
    # while this session was idle (or during a previous turn whose
    # mid-loop drains missed them).
    # The drained content is appended after ``message`` so the user's submitted
    # message remains the leading context (better UX: the user sent their primary
    # message first, queued follow-ups second).  The already-saved user message
    # in the DB is updated via update_message_content_by_sequence rather than
    # inserting a new row, because routes.py has already saved the user message
    # before the executor picks up the turn (using insert_pending_before_last +
    # persist_session_safe would add a duplicate row at sequence N+1).
    drained_at_start_pending = await drain_pending_safe(session_id, "[Baseline]")
    if drained_at_start_pending:
        logger.info(
            "[Baseline] Draining %d pending message(s) at turn start for session %s",
            len(drained_at_start_pending),
            session_id,
        )
        # Chronological combine: pending typed BEFORE this /stream
        # request's arrival go ahead of ``message``; race-path follow-ups
        # typed AFTER (queued while /stream was still processing) go
        # after.  See ``combine_pending_with_current`` for details.
        message = combine_pending_with_current(
            drained_at_start_pending,
            message,
            request_arrival_at=request_arrival_at,
        )
        # Update the in-memory content of the already-saved user message
        # and persist that update by sequence number.
        last_user_msg = next(
            (m for m in reversed(session.messages) if m.role == "user"), None
        )
        if last_user_msg is None or last_user_msg.sequence is None:
            # Defensive: routes.py always pre-saves the user message with a
            # sequence before dispatch, so this is unreachable under normal
            # flow. Raising instead of a warning-and-continue avoids silent
            # data loss (in-memory message diverges from the DB row, so the
            # queued chip would disappear from the UI after refresh without
            # a corresponding bubble).
            raise RuntimeError(
                f"[Baseline] Cannot persist turn-start pending injection: "
                f"last_user_msg={'missing' if last_user_msg is None else 'has no sequence'}"
            )
        last_user_msg.content = message
        await chat_db().update_message_content_by_sequence(
            session_id, last_user_msg.sequence, message
        )

    # Select model based on the per-request tier toggle (standard / advanced).
    # The path (fast vs extended_thinking) is already decided — we're in the
    # baseline (fast) path; ``mode`` is accepted for logging parity only.
    active_model = await _resolve_baseline_model(model, user_id)

    # --- E2B sandbox setup (feature parity with SDK path) ---
    e2b_sandbox = None
    e2b_api_key = config.active_e2b_api_key
    if e2b_api_key:
        try:
            from backend.copilot.tools.e2b_sandbox import get_or_create_sandbox

            e2b_sandbox = await get_or_create_sandbox(
                session_id,
                api_key=e2b_api_key,
                template=config.e2b_sandbox_template,
                timeout=config.e2b_sandbox_timeout,
                on_timeout=config.e2b_sandbox_on_timeout,
            )
        except Exception:
            logger.warning("[Baseline] E2B sandbox setup failed", exc_info=True)

    # --- Transcript support (feature parity with SDK path) ---
    transcript_builder = TranscriptBuilder()
    transcript_upload_safe = True

    # Build system prompt only on the first turn to avoid mid-conversation
    # changes from concurrent chats updating business understanding.
    # Use the pre-drain count so queued pending messages don't incorrectly
    # flip is_first_turn to False on an actual first turn.
    is_first_turn = _pre_drain_msg_count <= 1
    # Gate context fetch on both first turn AND user message so that assistant-
    # role calls (e.g. tool-result submissions) on the first turn don't trigger
    # a needless DB lookup for user understanding.
    should_inject_user_context = is_first_turn and is_user_message

    if should_inject_user_context:
        prompt_task = _build_system_prompt(user_id)
    else:
        prompt_task = _build_system_prompt(None)

    # Run download + prompt build concurrently — both are independent I/O
    # on the request critical path.  Use the pre-drain count so pending
    # messages drained at turn start don't spuriously trigger a transcript
    # load on an actual first turn.
    transcript_download: TranscriptDownload | None = None
    if user_id and _pre_drain_msg_count > 1:
        (
            (transcript_upload_safe, transcript_download),
            (base_system_prompt, understanding),
        ) = await asyncio.gather(
            _load_prior_transcript(
                user_id=user_id,
                session_id=session_id,
                session_messages=session.messages,
                transcript_builder=transcript_builder,
            ),
            prompt_task,
        )
    else:
        base_system_prompt, understanding = await prompt_task

    # Append user message to transcript after context injection below so the
    # transcript receives the prefixed message when user context is available.

    # NOTE: drained pending messages are folded into the current user
    # message's content (see the turn-start drain above), so the single
    # ``transcript_builder.append_user`` call below (covered by the
    # ``if message and is_user_message`` branch that appends
    # ``user_message_for_transcript or message``) already records the
    # combined text in the transcript. Do NOT also append drained items
    # individually here — on the ``transcript_download is None`` path
    # that would produce N separate pending entries plus the combined
    # entry, duplicating the pending content in the JSONL uploaded for
    # the next turn's ``--resume``.

    # Generate title for new sessions
    if is_user_message and not session.title:
        user_messages = [m for m in session.messages if m.role == "user"]
        if len(user_messages) == 1:
            first_message = user_messages[0].content or message or ""
            if first_message:
                task = asyncio.create_task(
                    _update_title_async(session_id, first_message, user_id)
                )
                _background_tasks.add(task)
                task.add_done_callback(_background_tasks.discard)

    message_id = str(uuid.uuid4())

    # Append tool documentation, technical notes, and Graphiti memory instructions
    graphiti_enabled = await is_enabled_for_user(user_id)

    graphiti_supplement = get_graphiti_supplement() if graphiti_enabled else ""
    # Append the builder-session block (graph id+name + full building guide)
    # AFTER the shared supplements so the system prompt is byte-identical
    # across turns of the same builder session — Claude's prompt cache keeps
    # the ~20KB guide warm for the whole session.  Empty string for
    # non-builder sessions keeps the cross-user cache hot.
    builder_session_suffix = await build_builder_system_prompt_suffix(session)
    system_prompt = (
        base_system_prompt
        + SHARED_TOOL_NOTES
        + graphiti_supplement
        + builder_session_suffix
    )

    # Warm context: pre-load relevant facts from Graphiti on first turn.
    # Use the pre-drain count so pending messages drained at turn start
    # don't prevent warm context injection on an actual first turn.
    # Stored here but injected into the user message (not the system prompt)
    # after openai_messages is built — keeps system prompt static for caching.
    warm_ctx: str | None = None
    if graphiti_enabled and user_id and _pre_drain_msg_count <= 1:
        from backend.copilot.graphiti.context import fetch_warm_context

        warm_ctx = await fetch_warm_context(user_id, message or "")

    # Context path: transcript content (compacted, isCompactSummary preserved) +
    # gap (DB messages after watermark) + current user turn.
    # This avoids re-reading the full session history from DB on every turn.
    # See extract_context_messages() in transcript.py for the shared primitive.
    prior_context = extract_context_messages(transcript_download, session.messages)
    messages_for_context = await _compress_session_messages(
        prior_context + ([session.messages[-1]] if session.messages else []),
        model=active_model,
    )

    # Build OpenAI message list from session history.
    # Include tool_calls on assistant messages and tool-role results so the
    # model retains full context of what tools were invoked and their outcomes.
    openai_messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt}
    ]
    for msg in messages_for_context:
        if msg.role == "assistant":
            entry: dict[str, Any] = {"role": "assistant"}
            if msg.content:
                entry["content"] = msg.content
            if msg.tool_calls:
                entry["tool_calls"] = msg.tool_calls
            if msg.content or msg.tool_calls:
                openai_messages.append(entry)
        elif msg.role == "tool" and msg.tool_call_id:
            openai_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content or "",
                }
            )
        elif msg.role == "user" and msg.content:
            openai_messages.append({"role": msg.role, "content": msg.content})

    # Inject user context into the first user message on first turn.
    # Done before attachment/URL injection so the context prefix lands at
    # the very start of the message content.
    user_message_for_transcript = message
    if should_inject_user_context:
        prefixed = await inject_user_context(
            understanding, message or "", session_id, session.messages
        )
        if prefixed is not None:
            # Reverse scan so we update the current turn's user message, not
            # the first (oldest) one when pending messages were drained.
            for msg in reversed(openai_messages):
                if msg["role"] == "user":
                    msg["content"] = prefixed
                    break
            user_message_for_transcript = prefixed
        else:
            logger.warning("[Baseline] No user message found for context injection")

    # Inject Graphiti warm context into the current turn's user message (not
    # the system prompt) so the system prompt stays static and cacheable.
    # warm_ctx is already wrapped in <temporal_context>.
    # Appended AFTER user_context so <user_context> stays at the very start.
    # Reverse scan so we update the current turn's user message, not the
    # oldest one when pending messages were drained.
    if warm_ctx:
        for msg in reversed(openai_messages):
            if msg["role"] == "user":
                existing = msg.get("content", "")
                if isinstance(existing, str):
                    msg["content"] = f"{existing}\n\n{warm_ctx}"
                break
        # Do NOT append warm_ctx to user_message_for_transcript — it would
        # persist stale temporal context into the transcript for future turns.

    # Inject the per-turn ``<builder_context>`` prefix when the session is
    # bound to a graph via ``metadata.builder_graph_id``.  Runs on every
    # user turn (not just the first) so the LLM always sees the live graph
    # snapshot — if the user edits the graph between turns, the next turn
    # carries the updated nodes/links. Only version + nodes + links here;
    # the static guide + graph id live in the system prompt via
    # ``build_builder_system_prompt_suffix`` (session-stable, prompt-cached).
    # Prepended AFTER any <user_context>/<memory_context>/<env_context> blocks
    # — same trust tier as those server-injected prefixes. Not persisted to
    # the transcript: the snapshot is stale-by-definition after the turn ends.
    if is_user_message and session.metadata.builder_graph_id:
        builder_block = await build_builder_context_turn_prefix(session, user_id)
        if builder_block:
            for msg in reversed(openai_messages):
                if msg["role"] == "user":
                    existing = msg.get("content", "")
                    if isinstance(existing, str):
                        msg["content"] = builder_block + existing
                    break

    # Append user message to transcript.
    # Always append when the message is present and is from the user,
    # even on duplicate-suppressed retries (is_new_message=False).
    # The loaded transcript may be stale (uploaded before the previous
    # attempt stored this message), so skipping it would leave the
    # transcript without the user turn, creating a malformed
    # assistant-after-assistant structure when the LLM reply is added.
    if message and is_user_message:
        transcript_builder.append_user(content=user_message_for_transcript or message)

    # --- File attachments (feature parity with SDK path) ---
    working_dir: str | None = None
    attachment_hint = ""
    image_blocks: list[dict[str, Any]] = []
    if file_ids and user_id:
        working_dir = tempfile.mkdtemp(prefix=f"copilot-baseline-{session_id[:8]}-")
        attachment_hint, image_blocks = await _prepare_baseline_attachments(
            file_ids, user_id, session_id, working_dir
        )

    # --- URL context ---
    context_hint = ""
    if context and context.get("url"):
        url = context["url"]
        content_text = context.get("content", "")
        if content_text:
            context_hint = (
                f"\n[The user shared a URL: {url}\nContent:\n{content_text[:8000]}]"
            )
        else:
            context_hint = f"\n[The user shared a URL: {url}]"

    # Append attachment + context hints and image blocks to the last user
    # message in a single reverse scan.
    extra_hint = attachment_hint + context_hint
    if extra_hint or image_blocks:
        for i in range(len(openai_messages) - 1, -1, -1):
            if openai_messages[i].get("role") == "user":
                existing = openai_messages[i].get("content", "")
                if isinstance(existing, str):
                    text = existing + "\n" + extra_hint if extra_hint else existing
                    if image_blocks:
                        parts: list[dict[str, Any]] = [{"type": "text", "text": text}]
                        for img in image_blocks:
                            parts.append(
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": (
                                            f"data:{img['source']['media_type']};"
                                            f"base64,{img['source']['data']}"
                                        )
                                    },
                                }
                            )
                        openai_messages[i]["content"] = parts
                    else:
                        openai_messages[i]["content"] = text
                break

    disabled_tool_groups: list[ToolGroup] = []
    if not graphiti_enabled:
        disabled_tool_groups.append("graphiti")
    tools = get_available_tools(disabled_groups=disabled_tool_groups)

    # --- Permission filtering ---
    if permissions is not None:
        tools = _filter_tools_by_permissions(tools, permissions)

    # Pre-mark cache_control on the last tool schema once per session.  The
    # tool set is static within a request, so doing this here (instead of in
    # _baseline_llm_caller) avoids re-copying ~43 tool dicts on every LLM
    # round of the tool-call loop.
    #
    # Applies to Anthropic AND Moonshot routes — OpenAI/Grok/Gemini 400
    # on the unknown ``cache_control`` field inside tool definitions, so
    # the gate stays narrow (see :func:`_supports_prompt_cache_markers`).
    if _supports_prompt_cache_markers(active_model):
        tools = cast(
            list[ChatCompletionToolParam], _mark_tools_with_cache_control(tools)
        )

    # Propagate execution context so tool handlers can read session-level flags.
    set_execution_context(
        user_id,
        session,
        sandbox=e2b_sandbox,
        sdk_cwd=working_dir,
        permissions=permissions,
    )

    yield StreamStart(messageId=message_id, sessionId=session_id)

    # Propagate user/session context to Langfuse so all LLM calls within
    # this request are grouped under a single trace with proper attribution.
    _trace_ctx: Any = None
    try:
        _trace_ctx = propagate_attributes(
            user_id=user_id,
            session_id=session_id,
            trace_name="copilot-baseline",
            tags=["baseline"],
        )
        _trace_ctx.__enter__()
    except Exception:
        logger.warning("[Baseline] Langfuse trace context setup failed")

    _stream_error = False  # Track whether an error occurred during streaming
    state = _BaselineStreamState(model=active_model)

    # Bind extracted module-level callbacks to this request's state/session
    # using functools.partial so they satisfy the Protocol signatures.
    _bound_llm_caller = partial(_baseline_llm_caller, state=state)

    # ``session`` is reassigned after each mid-turn ``persist_session_safe``
    # call (``upsert_chat_session`` returns a fresh ``model_copy``).  Holding
    # the object via ``partial(session=session)`` would pin tool executions
    # to the *original* object — any post-persist ``session.successful_agent_runs``
    # mutation from a run_agent tool call would then land on the stale copy
    # and be lost on the final persist.  Wrap in a 1-element holder and read
    # the current binding lazily so the executor always sees the latest session.
    _session_holder: list[ChatSession] = [session]

    async def _bound_tool_executor(
        tool_call: LLMToolCall, tools: Sequence[Any]
    ) -> ToolCallResult:
        return await _baseline_tool_executor(
            tool_call,
            tools,
            state=state,
            user_id=user_id,
            session=_session_holder[0],
        )

    _bound_conversation_updater = partial(
        _baseline_conversation_updater,
        transcript_builder=transcript_builder,
        model=active_model,
        state=state,
    )

    # Run the tool-call loop concurrently with the event consumer so
    # ``StreamReasoning*`` / ``StreamText*`` deltas emitted inside
    # ``_baseline_llm_caller`` reach the SSE wire DURING the upstream LLM
    # stream instead of only at iteration boundaries.  Any reasoning route
    # that streams for several minutes per round (extended thinking on
    # Anthropic / Moonshot / future providers) would otherwise freeze the
    # UI for the whole window before flushing the backlog in one burst.
    loop_result_holder: list[Any] = [None]
    loop_task: asyncio.Task[None] | None = None

    async def _run_tool_call_loop() -> None:
        # Read/write the current session via ``_session_holder`` so this
        # closure doesn't need to ``nonlocal session`` — pyright can't narrow
        # the outer ``session: ChatSession | None`` through a nested scope,
        # but the holder is typed non-optional after the preflight guard
        # above.
        try:
            async for loop_result in tool_call_loop(
                messages=openai_messages,
                tools=tools,
                llm_call=_bound_llm_caller,
                execute_tool=_bound_tool_executor,
                update_conversation=_bound_conversation_updater,
                max_iterations=_MAX_TOOL_ROUNDS,
            ):
                loop_result_holder[0] = loop_result
                # Inject any messages the user queued while the turn was
                # running.  ``tool_call_loop`` mutates ``openai_messages``
                # in-place, so appending here means the model sees the new
                # messages on its next LLM call.
                #
                # IMPORTANT: skip when the loop has already finished (no
                # more LLM calls are coming).  ``tool_call_loop`` yields
                # a final ``ToolCallLoopResult`` on both paths:
                #   - natural finish: ``finished_naturally=True``
                #   - hit max_iterations: ``finished_naturally=False``
                #                         and ``iterations >= max_iterations``
                # In either case the loop is about to return on the next
                # ``async for`` step, so draining here would silently
                # lose the message (the user sees 202 but the model never
                # reads the text).  Those messages stay in the buffer and
                # get picked up at the start of the next turn.
                is_final_yield = (
                    loop_result.finished_naturally
                    or loop_result.iterations >= _MAX_TOOL_ROUNDS
                )
                if is_final_yield:
                    continue
                try:
                    pending = await drain_pending_messages(session_id)
                except Exception:
                    logger.warning(
                        "[Baseline] mid-loop drain_pending_messages failed for "
                        "session %s",
                        session_id,
                        exc_info=True,
                    )
                    pending = []
                if pending:
                    # Flush any buffered assistant/tool messages from completed
                    # rounds into session.messages BEFORE appending the pending
                    # user message.  ``_baseline_conversation_updater`` only
                    # records assistant+tool rounds into ``state.session_messages``
                    # — they are normally batch-flushed in the finally block.
                    # Without this in-order flush, the mid-loop pending user
                    # message lands before the preceding round's assistant/tool
                    # entries, producing chronologically-wrong session.messages
                    # on persist (user interposed between an assistant tool_call
                    # and its tool-result), which breaks OpenAI tool-call ordering
                    # invariants on the next turn's replay.
                    #
                    # Also persist any assistant text from text-only rounds (rounds
                    # with no tool calls, which ``_baseline_conversation_updater``
                    # does NOT record in session_messages).  If we only update
                    # ``_flushed_assistant_text_len`` without persisting the text,
                    # that text is silently lost: the finally block only appends
                    # assistant_text[_flushed_assistant_text_len:], so text generated
                    # before this drain never reaches session.messages.
                    recorded_text = "".join(
                        m.content or ""
                        for m in state.session_messages
                        if m.role == "assistant"
                    )
                    unflushed_text = state.assistant_text[
                        state._flushed_assistant_text_len :
                    ]
                    text_only_text = (
                        unflushed_text[len(recorded_text) :]
                        if unflushed_text.startswith(recorded_text)
                        else unflushed_text
                    )
                    current_session = _session_holder[0]
                    if text_only_text.strip():
                        current_session.messages.append(
                            ChatMessage(role="assistant", content=text_only_text)
                        )
                    for _buffered in state.session_messages:
                        current_session.messages.append(_buffered)
                    state.session_messages.clear()
                    # Record how much assistant_text has been covered by the
                    # structured entries just flushed, so the finally block's
                    # final-text dedup doesn't re-append rounds already persisted.
                    state._flushed_assistant_text_len = len(state.assistant_text)

                    # Persist the assistant/tool flush BEFORE the pending append
                    # so a later pending-persist failure can roll back the
                    # pending rows without also discarding LLM output.
                    current_session = await persist_session_safe(
                        current_session, "[Baseline]"
                    )
                    # ``upsert_chat_session`` may return a *new* ``ChatSession``
                    # instance (e.g. when a concurrent title update has written a
                    # newer title to Redis, it returns ``session.model_copy``).
                    # Keep ``_session_holder`` in sync so subsequent tool rounds
                    # executed via ``_bound_tool_executor`` see the fresh session
                    # — any tool-side mutations on the stale object would be
                    # discarded when the new one is persisted in the ``finally``.
                    _session_holder[0] = current_session

                    # ``format_pending_as_user_message`` embeds file attachments
                    # and context URL/page content into the content string so
                    # the in-session transcript is a faithful copy of what the
                    # model actually saw.  We also mirror each push into
                    # ``openai_messages`` so the model's next LLM round sees it.
                    #
                    # Pre-compute the formatted dicts once so both the openai
                    # messages append and the content_of lookup inside the
                    # shared helper use the same string — and so ``on_rollback``
                    # can trim ``openai_messages`` to the recorded anchor.
                    formatted_by_pm = {
                        id(pm): format_pending_as_user_message(pm) for pm in pending
                    }
                    _openai_anchor = len(openai_messages)
                    for pm in pending:
                        openai_messages.append(formatted_by_pm[id(pm)])

                    def _trim_openai_on_rollback(_session_anchor: int) -> None:
                        del openai_messages[_openai_anchor:]

                    await persist_pending_as_user_rows(
                        current_session,
                        transcript_builder,
                        pending,
                        log_prefix="[Baseline]",
                        content_of=lambda pm: formatted_by_pm[id(pm)]["content"],
                        on_rollback=_trim_openai_on_rollback,
                    )
        finally:
            # Always post the sentinel so the outer consumer exits — even if
            # ``tool_call_loop`` raised.  ``_baseline_llm_caller``'s own
            # finally block has already pushed ``StreamReasoningEnd`` /
            # ``StreamTextEnd`` / ``StreamFinishStep`` at this point, so the
            # sentinel only terminates the consumer; it does not suppress
            # any still-unflushed events.
            state.pending_events.put_nowait(None)

    loop_task = asyncio.create_task(_run_tool_call_loop())
    try:
        while True:
            evt = await state.pending_events.get()
            if evt is None:
                break
            yield evt
        # Sentinel received — surface any exception the inner task hit.
        await loop_task
        loop_result = loop_result_holder[0]
        if loop_result and not loop_result.finished_naturally:
            limit_msg = (
                f"Exceeded {_MAX_TOOL_ROUNDS} tool-call rounds "
                "without a final response."
            )
            logger.error("[Baseline] %s", limit_msg)
            yield StreamError(
                errorText=limit_msg,
                code="baseline_tool_round_limit",
            )
    except Exception as e:
        _stream_error = True
        error_msg = str(e) or type(e).__name__
        logger.error("[Baseline] Streaming error: %s", error_msg, exc_info=True)
        # Drain any queued tail events (reasoning/text close + finish step)
        # that ``_baseline_llm_caller``'s finally block pushed before the
        # sentinel arrived — without this the frontend would be missing the
        # matching end / finish parts for the partial round.
        while not state.pending_events.empty():
            evt = state.pending_events.get_nowait()
            if evt is not None:
                yield evt
        yield StreamError(errorText=error_msg, code="baseline_error")
        # Still persist whatever we got
    finally:
        # Cancel the inner task if we're unwinding early (client disconnect,
        # unexpected error in the consumer) so it doesn't keep streaming
        # tokens into a dead queue.
        if loop_task is not None and not loop_task.done():
            loop_task.cancel()
            try:
                await loop_task
            except (asyncio.CancelledError, Exception):
                pass
        # Re-sync the outer ``session`` binding in case the inner task
        # reassigned it via a mid-loop ``persist_session_safe`` call.
        session = _session_holder[0]

        # In-flight tool-call announcements are only meaningful for the
        # current turn; clear at the top of the outer finally so the next
        # turn starts with a clean scratch buffer even if one of the
        # awaited cleanup steps below (usage persistence, session upsert,
        # transcript upload) raises.  The buffer is a process-local scratch
        # set — if we leak it into the next turn the guide-read guard would
        # observe a phantom in-flight call and skip its gate, so this must
        # run unconditionally.
        session.clear_inflight_tool_calls()

        # Pending messages are drained atomically at turn start and
        # between tool rounds, so there's nothing to clear in finally.
        # Any message pushed after the final drain window stays in the
        # buffer and gets picked up at the start of the next turn.

        # Set cost attributes on OTEL span before closing
        if _trace_ctx is not None:
            try:
                span = otel_trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute(
                        "gen_ai.usage.prompt_tokens", state.turn_prompt_tokens
                    )
                    span.set_attribute(
                        "gen_ai.usage.completion_tokens",
                        state.turn_completion_tokens,
                    )
                    if state.cost_usd is not None:
                        span.set_attribute("gen_ai.usage.cost_usd", state.cost_usd)
            except Exception:
                logger.debug("[Baseline] Failed to set OTEL cost attributes")
            try:
                _trace_ctx.__exit__(None, None, None)
            except Exception:
                logger.warning("[Baseline] Langfuse trace context teardown failed")

        # Fallback: estimate tokens via tiktoken when the provider does
        # not honour stream_options={"include_usage": True}.
        # Count the full message list (system + history + turn) since
        # each API call sends the complete context window.
        # NOTE: This estimates one round's prompt tokens. Multi-round tool-calling
        # turns consume prompt tokens on each API call, so the total is underestimated.
        # Skip fallback when an error occurred and no output was produced —
        # charging rate-limit tokens for completely failed requests is unfair.
        if (
            state.turn_prompt_tokens == 0
            and state.turn_completion_tokens == 0
            and not (_stream_error and not state.assistant_text)
        ):
            state.turn_prompt_tokens = max(
                estimate_token_count(openai_messages, model=active_model), 1
            )
            state.turn_completion_tokens = estimate_token_count_str(
                state.assistant_text, model=active_model
            )
            logger.info(
                "[Baseline] No streaming usage reported; estimated tokens: "
                "prompt=%d, completion=%d",
                state.turn_prompt_tokens,
                state.turn_completion_tokens,
            )
        # Persist token usage to session and record for rate limiting.
        # When prompt_tokens_details.cached_tokens is reported, subtract
        # them from prompt_tokens to get the uncached count so the cost
        # breakdown stays accurate.
        uncached_prompt = state.turn_prompt_tokens
        if state.turn_cache_read_tokens > 0:
            uncached_prompt = max(
                0, state.turn_prompt_tokens - state.turn_cache_read_tokens
            )
        await persist_and_record_usage(
            session=session,
            user_id=user_id,
            prompt_tokens=uncached_prompt,
            completion_tokens=state.turn_completion_tokens,
            cache_read_tokens=state.turn_cache_read_tokens,
            cache_creation_tokens=state.turn_cache_creation_tokens,
            log_prefix="[Baseline]",
            cost_usd=state.cost_usd,
            model=active_model,
        )

        # Persist structured tool-call history (assistant + tool messages)
        # collected by the conversation updater, then the final text response.
        for msg in state.session_messages:
            session.messages.append(msg)
        # Append the final assistant text (from the last LLM call that had
        # no tool calls, i.e. the natural finish).  Only add it if the
        # conversation updater didn't already record it as part of a
        # tool-call round (which would have empty response_text).
        # Only consider assistant text produced AFTER the last mid-loop
        # flush.  ``_flushed_assistant_text_len`` tracks the prefix already
        # persisted via structured session_messages during mid-loop pending
        # drains; including it here would duplicate those rounds.
        final_text = state.assistant_text[state._flushed_assistant_text_len :]
        if state.session_messages:
            # Strip text already captured in tool-call round messages
            recorded = "".join(
                m.content or "" for m in state.session_messages if m.role == "assistant"
            )
            if final_text.startswith(recorded):
                final_text = final_text[len(recorded) :]
        if final_text.strip():
            session.messages.append(ChatMessage(role="assistant", content=final_text))
        try:
            await upsert_chat_session(session)
        except Exception as persist_err:
            logger.error("[Baseline] Failed to persist session: %s", persist_err)

        # --- Graphiti: ingest conversation turn for temporal memory ---
        if graphiti_enabled and user_id and message and is_user_message:
            from backend.copilot.graphiti.ingest import enqueue_conversation_turn

            # Pass only the final assistant reply (after stripping tool-loop
            # chatter) so derived-finding distillation sees the substantive
            # response, not intermediate tool-planning text.
            _ingest_task = asyncio.create_task(
                enqueue_conversation_turn(
                    user_id,
                    session_id,
                    message,
                    assistant_msg=final_text if state else "",
                )
            )
            _background_tasks.add(_ingest_task)
            _ingest_task.add_done_callback(_background_tasks.discard)

        # --- Upload transcript for next-turn continuity ---
        # Backfill partial assistant text that wasn't recorded by the
        # conversation updater (e.g. when the stream aborted mid-round).
        # Without this, mode-switching after a failed turn would lose
        # the partial assistant response from the transcript.
        if _stream_error and state.assistant_text:
            if transcript_builder.last_entry_type != "assistant":
                transcript_builder.append_assistant(
                    content_blocks=[{"type": "text", "text": state.assistant_text}],
                    model=active_model,
                    stop_reason=STOP_REASON_END_TURN,
                )

        if user_id and should_upload_transcript(user_id, transcript_upload_safe):
            await _upload_final_transcript(
                user_id=user_id,
                session_id=session_id,
                transcript_builder=transcript_builder,
                session_msg_count=len(session.messages),
            )

        # Clean up the ephemeral working directory used for file attachments.
        if working_dir is not None:
            shutil.rmtree(working_dir, ignore_errors=True)

    # Yield usage and finish AFTER try/finally (not inside finally).
    # PEP 525 prohibits yielding from finally in async generators during
    # aclose() — doing so raises RuntimeError on client disconnect.
    # On GeneratorExit the client is already gone, so unreachable yields
    # are harmless; on normal completion they reach the SSE stream.
    if state.turn_prompt_tokens > 0 or state.turn_completion_tokens > 0:
        # Report uncached prompt tokens to match what was billed — cached tokens
        # are excluded so the frontend display is consistent with cost_usd.
        billed_prompt = max(0, state.turn_prompt_tokens - state.turn_cache_read_tokens)
        yield StreamUsage(
            prompt_tokens=billed_prompt,
            completion_tokens=state.turn_completion_tokens,
            total_tokens=billed_prompt + state.turn_completion_tokens,
            cache_read_tokens=state.turn_cache_read_tokens,
            cache_creation_tokens=state.turn_cache_creation_tokens,
        )

    yield StreamFinish()