async def stream_chat_completion_sdk(
    session_id: str,
    message: str | None = None,
    is_user_message: bool = True,
    user_id: str | None = None,
    session: ChatSession | None = None,
    file_ids: list[str] | None = None,
    permissions: "CopilotPermissions | None" = None,
    mode: CopilotMode | None = None,
    model: CopilotLlmModel | None = None,
    request_arrival_at: float = 0.0,
    **_kwargs: Any,
) -> AsyncGenerator[StreamBaseResponse, None]:
    """Stream chat completion using Claude Agent SDK.

    Args:
        file_ids: Optional workspace file IDs attached to the user's message.
            Images are embedded as vision content blocks; other files are
            saved to the SDK working directory for the Read tool.
        mode: Accepted for signature compatibility with the baseline path.
            The SDK path does not currently branch on this value.
        model: Per-request model preference from the frontend toggle.
            'advanced' → Claude Opus; 'standard' → global config default.
            Takes priority over per-user LaunchDarkly targeting.
    """
    _ = mode  # SDK path ignores the requested mode.

    if session is None:
        session = await get_chat_session(session_id, user_id)

    if not session:
        raise NotFoundError(
            f"Session {session_id} not found. Please create a new session first."
        )

    # Type narrowing: session is guaranteed ChatSession after the check above
    session = cast(ChatSession, session)

    # Clean up ALL trailing error markers from previous turn before starting
    # a new turn.  Multiple markers can accumulate when a mid-stream error is
    # followed by a cleanup error in __aexit__ (both append a marker).
    while (
        len(session.messages) > 0
        and session.messages[-1].role == "assistant"
        and session.messages[-1].content
        and (
            COPILOT_ERROR_PREFIX in session.messages[-1].content
            or COPILOT_RETRYABLE_ERROR_PREFIX in session.messages[-1].content
        )
    ):
        logger.info(
            "[SDK] [%s] Removing stale error marker from previous turn",
            session_id[:12],
        )
        session.messages.pop()

    # Drop orphan tool_use + trailing stop-marker rows left by a previous
    # Stop mid-tool-call so the next turn's --resume transcript is well-formed.
    prune_orphan_tool_calls(session.messages, log_prefix=f"[SDK] [{session_id[:12]}]")

    # Strip any user-injected <user_context> tags on every turn.
    # Only the server-injected prefix on the first message is trusted.
    if message:
        message = strip_user_context_tags(message)

    _user_message_appended = maybe_append_user_message(
        session, message, is_user_message
    )
    if _user_message_appended and is_user_message:
        track_user_message(
            user_id=user_id,
            session_id=session_id,
            message_length=len(message or ""),
        )

    # Structured log prefix: [SDK][<session>][T<turn>]
    # Turn = number of user messages (1-based), computed AFTER appending the new message.
    turn = sum(1 for m in session.messages if m.role == "user")
    log_prefix = f"[SDK][{session_id[:12]}][T{turn}]"

    # Persist the appended user message to DB immediately so page refreshes
    # during a long-running turn (e.g. auto-continue whose sleep/bash call
    # blocks for minutes) show the user bubble. routes.py pre-saves the
    # user message before direct POSTs so maybe_append_user_message returns
    # False there (duplicate) — this branch only fires for internal callers
    # that did NOT pre-save, most notably the auto-continue recursive call
    # below.
    #
    # If the persist fails, roll back the in-memory append: otherwise
    # session.messages[-1] carries a ``sequence=None`` ghost row, and a
    # later turn-start drain (from a pending message queued during this
    # turn) would trip the "no sequence" RuntimeError and crash the turn.
    if _user_message_appended and is_user_message:
        session = await persist_session_safe(session, log_prefix)
        if session.messages and session.messages[-1].sequence is None:
            # Eager persist swallowed a transient DB failure and left the
            # in-memory append without a sequence. Roll back so the session
            # stays consistent with the DB and raise so the caller can
            # re-queue any drained content. Without this, a later
            # turn-start drain would trip the "no sequence" RuntimeError
            # and lose the fresh pending messages it just LPOPed.
            session.messages.pop()
            raise RuntimeError(
                f"{log_prefix} Eager persist of user message failed; "
                f"in-memory append rolled back"
            )

    # Generate title for new sessions (first user message)
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
    stream_id = str(uuid.uuid4())
    ended_with_stream_error = False
    e2b_sandbox = None
    use_resume = False
    resume_file: str | None = None
    transcript_builder = TranscriptBuilder()
    sdk_cwd = ""
    # True when transcript_builder represents a full prefix of session history.
    # First turn (<=1 prior message) is fully covered even without a download.
    # Set to True when load_previous succeeds; stays False when download fails
    # on a session with prior messages, preventing a partial upload that would
    # mislead _build_query_message into skipping gap reconstruction next turn.
    transcript_covers_prefix = True

    # Acquire stream lock to prevent concurrent streams to the same session
    lock = AsyncClusterLock(
        redis=await get_redis_async(),
        key=f"{STREAM_LOCK_PREFIX}{session_id}",
        owner_id=stream_id,
        timeout=config.stream_lock_ttl,
    )

    lock_owner = await lock.try_acquire()
    if lock_owner != stream_id:
        # Another stream is active
        logger.warning(
            "%s Session already has an active stream: %s", log_prefix, lock_owner
        )
        yield StreamError(
            errorText="Another stream is already active for this session. "
            "Please wait or stop it.",
            code="stream_already_active",
        )
        return

    # OTEL context manager — initialized inside the try and cleaned up in finally.
    _otel_ctx: Any = None
    skip_transcript_upload = False
    has_history = len(session.messages) > 1
    transcript_content: str = ""
    state: _RetryState | None = None

    # Token usage accumulators — populated from ResultMessage at end of turn
    turn_prompt_tokens = 0  # uncached input tokens only
    turn_completion_tokens = 0
    turn_cache_read_tokens = 0
    turn_cache_creation_tokens = 0
    turn_cost_usd: float | None = None
    graphiti_enabled = False
    pre_attempt_msg_count = 0
    # Defaults ensure the finally block can always reference these safely even when
    # an early return (e.g. sdk_cwd error) skips their normal assignment below.
    sdk_model: str | None = None
    # Wall-clock timestamp captured before the CLI runs so the
    # OpenRouter reconcile can filter subagent JSONLs by mtime — only
    # files created during THIS turn contribute gen-IDs.  Without this
    # the sweep would pick up prior turns' compaction files that persist
    # under ``<session_id>/subagents/``, double-billing the user.
    turn_start_ts = time.time()

    # Make sure there is no more code between the lock acquisition and try-block.
    try:
        # Build system prompt (reuses non-SDK path with Langfuse support).
        # Pre-compute the cwd here so the exact working directory path can be
        # injected into the supplement instead of the generic placeholder.
        # Catch ValueError early so the failure yields a clean StreamError rather
        # than propagating outside the stream error-handling path.
        try:
            sdk_cwd = _make_sdk_cwd(session_id)
            os.makedirs(sdk_cwd, exist_ok=True)
        except (ValueError, OSError) as e:
            logger.error("%s Invalid SDK cwd: %s", log_prefix, e)
            yield StreamError(
                errorText="Unable to initialize working directory.",
                code="sdk_cwd_error",
            )
            return
        # --- Run independent async I/O operations in parallel ---
        # E2B sandbox setup, system prompt build (Langfuse + DB), and transcript
        # download are independent network calls.  Running them concurrently
        # saves ~200-500ms compared to sequential execution.

        async def _setup_e2b():
            """Set up E2B sandbox if configured, return sandbox or None."""
            if not (e2b_api_key := config.active_e2b_api_key):
                if config.use_e2b_sandbox:
                    logger.warning(
                        "[E2B] [%s] E2B sandbox enabled but no API key configured "
                        "(CHAT_E2B_API_KEY / E2B_API_KEY) — falling back to bubblewrap",
                        session_id[:12],
                    )
                return None
            try:
                sandbox = await get_or_create_sandbox(
                    session_id,
                    api_key=e2b_api_key,
                    template=config.e2b_sandbox_template,
                    timeout=config.e2b_sandbox_timeout,
                    on_timeout=config.e2b_sandbox_on_timeout,
                )
            except Exception as e2b_err:
                logger.error(
                    "[E2B] [%s] Setup failed: %s",
                    session_id[:12],
                    e2b_err,
                    exc_info=True,
                )
                return None

            return sandbox

        e2b_sandbox, (base_system_prompt, understanding) = await asyncio.gather(
            _setup_e2b(),
            _build_system_prompt(user_id if not has_history else None),
        )

        use_e2b = e2b_sandbox is not None
        # Append appropriate supplement (Claude gets tool schemas automatically)

        graphiti_enabled = await is_enabled_for_user(user_id)

        graphiti_supplement = get_graphiti_supplement() if graphiti_enabled else ""
        # Append the builder-session block (graph id+name + full building
        # guide) AFTER the shared supplements so the system prompt is
        # byte-identical across turns of the same builder session — Claude's
        # prompt cache keeps the ~20KB guide warm for the whole session.
        # Empty string for non-builder sessions preserves cross-user caching.
        builder_session_suffix = await build_builder_system_prompt_suffix(session)
        system_prompt = (
            base_system_prompt
            + get_sdk_supplement(use_e2b=use_e2b)
            + graphiti_supplement
            + builder_session_suffix
        )

        # Warm context: pre-load relevant facts from Graphiti on first turn.
        # Stored here and injected into the first user message (not the system
        # prompt) so the system prompt stays identical across all users and
        # sessions, enabling cross-session Anthropic prompt-cache hits.
        warm_ctx = ""
        if graphiti_enabled and user_id and len(session.messages) <= 1:
            from ..graphiti.context import fetch_warm_context

            warm_ctx = await fetch_warm_context(user_id, message or "") or ""

        # Restore CLI session — single GCS round-trip covers both --resume and builder state.
        # message_count watermark lives in the companion .meta.json alongside the session file.
        _restore = await _restore_cli_session_for_turn(
            user_id, session_id, session, sdk_cwd, transcript_builder, log_prefix
        )
        transcript_content = _restore.transcript_content
        transcript_covers_prefix = _restore.transcript_covers_prefix
        use_resume = _restore.use_resume
        resume_file = _restore.resume_file
        transcript_msg_count = _restore.transcript_msg_count
        restore_context_messages = _restore.context_messages

        yield StreamStart(messageId=message_id, sessionId=session_id)

        set_execution_context(
            user_id,
            session,
            sandbox=e2b_sandbox,
            sdk_cwd=sdk_cwd,
            permissions=permissions,
        )

        # Fail fast when no API credentials are available at all.
        # sdk_cwd routes the CLI's temp dir into the per-session workspace
        # so sub-agent output files land inside sdk_cwd (see build_sdk_env).
        sdk_env = build_sdk_env(session_id=session_id, user_id=user_id, sdk_cwd=sdk_cwd)

        if not config.api_key and not config.use_claude_code_subscription:
            raise RuntimeError(
                "No API key configured. Set OPEN_ROUTER_API_KEY, "
                "CHAT_API_KEY, or ANTHROPIC_API_KEY for API access, "
                "or CHAT_USE_CLAUDE_CODE_SUBSCRIPTION=true to use "
                "Claude Code CLI subscription (requires `claude login`)."
            )

        mcp_server = create_copilot_mcp_server(use_e2b=use_e2b)

        # Resolve model (request tier → LD per-user override → config default).
        sdk_model = await _resolve_sdk_model_for_request(model, session_id, user_id)

        # Track SDK-internal compaction (PreCompact hook → start, next msg → end)
        compaction = CompactionTracker()

        security_hooks = create_security_hooks(
            user_id,
            sdk_cwd=sdk_cwd,
            max_subtasks=config.claude_agent_max_subtasks,
            on_compact=compaction.on_compact,
        )

        disabled_tool_groups: list[ToolGroup] = []
        if not graphiti_enabled:
            disabled_tool_groups.append("graphiti")

        if permissions is not None:
            allowed, disallowed = apply_tool_permissions(
                permissions, use_e2b=use_e2b, disabled_groups=disabled_tool_groups
            )
        else:
            allowed = get_copilot_tool_names(
                use_e2b=use_e2b, disabled_groups=disabled_tool_groups
            )
            disallowed = get_sdk_disallowed_tools(use_e2b=use_e2b)

        def _on_stderr(line: str) -> None:
            """Log a stderr line emitted by the Claude CLI subprocess."""
            nonlocal fallback_model_activated_per_attempt
            sid = session_id[:12] if session_id else "?"
            logger.info("[SDK] [%s] CLI stderr: %s", sid, line.rstrip())
            # Detect SDK fallback-model activation via the module-level pure
            # helper so the detection logic can be unit-tested independently.
            # Sets the per-attempt flag which is preserved across transient
            # retries so the user notification is never lost.
            if not fallback_model_activated_per_attempt and _is_fallback_stderr(line):
                fallback_model_activated_per_attempt = True
                logger.warning(
                    "[SDK] [%s] Fallback model activated — primary model "
                    "overloaded, switching to fallback",
                    sid,
                )

        # Use SystemPromptPreset with exclude_dynamic_sections=True on
        # every turn — including resumed ones — so all turns share the
        # same static prefix and hit the cross-user prompt cache.
        #
        # Requires CLI ≥ 2.1.98 (older CLIs crash when excludeDynamicSections
        # is combined with --resume).  claude-agent-sdk >= 0.1.64 bundles
        # CLI 2.1.116, so the pin in pyproject.toml is sufficient — no
        # external install or env-var override needed.
        system_prompt_value = _build_system_prompt_value(
            system_prompt,
            cross_user_cache=config.claude_agent_cross_user_prompt_cache,
        )

        sdk_options_kwargs: dict[str, Any] = {
            "system_prompt": system_prompt_value,
            "mcp_servers": {"copilot": mcp_server},
            "allowed_tools": allowed,
            "disallowed_tools": disallowed,
            "hooks": security_hooks,
            "cwd": sdk_cwd,
            "max_buffer_size": config.claude_agent_max_buffer_size,
            "stderr": _on_stderr,
            # --- P0 guardrails ---
            # fallback_model: SDK auto-retries with this cheaper model on
            # 529 (overloaded) errors, avoiding user-visible failures.
            "fallback_model": _resolve_fallback_model(),
            # max_turns: hard cap on agentic tool-use loops per query to
            # prevent runaway execution from burning budget.
            "max_turns": config.claude_agent_max_turns,
            # max_budget_usd: per-query spend ceiling enforced by the CLI.
            "max_budget_usd": config.claude_agent_max_budget_usd,
        }
        # max_thinking_tokens: cap extended thinking output per LLM call.
        # Thinking tokens are billed at output rate ($75/M for Opus) and
        # account for ~54% of total cost.  8192 is the default.
        # Intentionally sent for all models including Sonnet — the CLI
        # silently ignores this field for non-Opus models (those without
        # native extended thinking), so it is safe to pass unconditionally.
        # Setting to 0 acts as the kill switch (same as baseline): omit the
        # kwarg so the CLI falls back to its default (extended thinking off).
        if config.claude_agent_max_thinking_tokens > 0:
            sdk_options_kwargs["max_thinking_tokens"] = (
                config.claude_agent_max_thinking_tokens
            )
        # effort: only set for models with extended thinking (Opus).
        # Setting effort on Sonnet causes <internal_reasoning> tag leaks.
        if config.claude_agent_thinking_effort:
            sdk_options_kwargs["effort"] = config.claude_agent_thinking_effort
        if sdk_model:
            sdk_options_kwargs["model"] = sdk_model
        if config.sdk_include_partial_messages:
            # Opt into per-token streaming — the CLI emits raw Anthropic
            # ``content_block_delta`` events as ``StreamEvent`` messages
            # ahead of each summary ``AssistantMessage`` so reasoning and
            # text land on the wire token-by-token (matching the baseline
            # path's UX shipped in #12873).  ``SDKResponseAdapter`` consumes
            # the partial stream via ``_handle_stream_event`` and emits
            # only the tail diff from the subsequent summary, so content
            # never double-emits and a summary-only short block still
            # reaches the UI.
            sdk_options_kwargs["include_partial_messages"] = True

        if sdk_env:
            sdk_options_kwargs["env"] = sdk_env
        if use_resume and resume_file:
            # --resume {uuid} implies the session UUID — do NOT also pass
            # --session-id here.  CLI >=2.1.97 rejects the combination of
            # --session-id + --resume unless --fork-session is also given.
            sdk_options_kwargs["resume"] = resume_file
        else:
            # Set session_id whenever NOT resuming so the CLI writes the
            # native session file to a predictable path for
            # upload_transcript() after the turn.  This covers:
            #   • T1 fresh: no prior history, first SDK turn.
            #   • Mode-switch T1: has_history=True (prior baseline turns in
            #     DB) but no CLI session file was ever uploaded — the CLI has
            #     never been invoked with this session_id before.
            #   • T2+ without --resume (restore failed): no session file was
            #     restored to local storage (download_transcript returned
            #     None), so no conflict with an existing file.
            # When --resume is active the session_id is already implied by
            # the resume file; passing it again would be rejected by the CLI.
            sdk_options_kwargs["session_id"] = session_id
        # Optional explicit Claude Code CLI binary path (decouples the
        # bundled SDK version from the CLI version we run — needed because
        # the CLI bundled in 0.1.46+ is broken against OpenRouter).  Falls
        # back to the bundled binary when unset.
        if config.claude_agent_cli_path:
            sdk_options_kwargs["cli_path"] = config.claude_agent_cli_path

        options = ClaudeAgentOptions(**sdk_options_kwargs)  # type: ignore[arg-type]  # dynamic kwargs

        adapter = SDKResponseAdapter(
            message_id=message_id,
            session_id=session_id,
            render_reasoning_in_ui=config.render_reasoning_in_ui,
        )

        # Propagate user_id/session_id as OTEL context attributes so the
        # langsmith tracing integration attaches them to every span.  This
        # is what Langfuse (or any OTEL backend) maps to its native
        # user/session fields.
        _user_tier = await get_user_tier(user_id) if user_id else None
        _otel_metadata: dict[str, str] = {
            "resume": str(use_resume),
            "conversation_turn": str(turn),
        }
        if _user_tier:
            _otel_metadata["subscription_tier"] = _user_tier.value

        _otel_ctx = propagate_attributes(
            user_id=user_id,
            session_id=session_id,
            trace_name="copilot-sdk",
            tags=["sdk"],
            metadata=_otel_metadata,
        )
        _otel_ctx.__enter__()

        current_message = message or ""
        if not current_message and session.messages:
            last_user = [m for m in session.messages if m.role == "user"]
            if last_user:
                current_message = last_user[-1].content or ""

        # Capture the message count *before* draining so _build_query_message
        # can compute the gap slice without including the newly-drained pending
        # messages.  Pending messages are both appended to session.messages AND
        # concatenated into current_message; without the ceiling the gap slice
        # would extend into the pending messages and duplicate them in the
        # model's input context (gap_context + current_message both containing
        # them).
        _pre_drain_msg_count = len(session.messages)

        # Drain any messages the user queued via POST /messages/pending
        # while the previous turn was running (or since the session was
        # idle).  Messages are drained ATOMICALLY — one LPOP with count
        # removes them all at once, so a concurrent push lands *after*
        # the drain and stays queued for the next turn instead of being
        # lost between LPOP and clear.  File IDs and context are
        # preserved via format_pending_as_user_message.
        #
        # The drained content is combined in chronological (typing) order:
        # pending messages were queued DURING the previous turn, so they
        # were typed BEFORE the current /stream message.  Putting pending
        # first — ``pending → current`` — matches the order the user
        # actually sent them and avoids the "I typed A then B but it shows
        # up as B then A" confusion.  The already-saved user message in
        # the DB is updated via update_message_content_by_sequence to
        # include the pending texts, avoiding a duplicate INSERT that
        # would occur if we used insert_pending_before_last +
        # persist_session_safe (routes.py has already saved the user
        # message at sequence N before the executor runs, so an
        # incremental upsert would write a second copy at N+1).
        pending_messages = await drain_pending_safe(session_id, log_prefix)
        if pending_messages:
            logger.info(
                "%s Draining %d pending message(s) at turn start",
                log_prefix,
                len(pending_messages),
            )
            # Chronological combine: items typed BEFORE this request
            # arrived go ahead of ``current_message``; items typed AFTER
            # (race path, queued while /stream was still processing) go
            # after.
            current_message = combine_pending_with_current(
                pending_messages,
                current_message,
                request_arrival_at=request_arrival_at,
            )
            # Update the in-memory content of the already-saved user message
            # and persist that update to the DB by sequence number.  This
            # avoids inserting an extra row — the user message was already
            # written at its sequence by append_and_save_message in routes.py.
            last_user_msg = next(
                (m for m in reversed(session.messages) if m.role == "user"), None
            )
            if last_user_msg is None or last_user_msg.sequence is None:
                # Defensive: routes.py always pre-saves the user message with
                # a sequence before dispatch, so this is unreachable under
                # normal flow. Raising instead of a warning-and-continue
                # avoids silent data loss (in-memory diverges from DB row,
                # so the queued chip would disappear from the UI after
                # refresh without a corresponding bubble).
                raise RuntimeError(
                    f"{log_prefix} Cannot persist turn-start pending injection: "
                    f"last_user_msg={'missing' if last_user_msg is None else 'has no sequence'}"
                )
            last_user_msg.content = current_message
            await chat_db().update_message_content_by_sequence(
                session_id, last_user_msg.sequence, current_message
            )

        if not current_message.strip():
            yield StreamError(
                errorText="Message cannot be empty.",
                code="empty_prompt",
            )
            return

        # Strip any user-injected <user_context> tags from current_message.
        # On --resume, current_message may come from session history which was
        # already sanitized on the original turn; strip again as defence-in-depth.
        current_message = strip_user_context_tags(current_message)

        # On the first turn inject user context into the message before building
        # the query so that _build_query_message sees the full prefixed content.
        # The system prompt is now static (same for all users) so the LLM can
        # cache it across sessions.
        #
        # On resume (has_history=True) we intentionally skip re-injection: the
        # transcript already contains the <user_context> and <memory_context>
        # prefixes from the original turn (persisted to the DB via
        # inject_user_context), so the SDK replay carries context continuity
        # without us prepending them again.
        if not has_history:
            # Build env_ctx for the working directory and pass it into
            # inject_user_context so it is prepended AFTER
            # sanitize_user_supplied_context runs — preventing the trusted
            # <env_context> block from being stripped by the sanitizer.
            env_ctx_content = ""
            if not use_e2b and sdk_cwd:
                env_ctx_content = f"working_dir: {sdk_cwd}"
            # Pass warm_ctx and env_ctx to inject_user_context so they are
            # prepended AFTER sanitize_user_supplied_context runs — preventing
            # trusted server-injected blocks from being stripped by the sanitizer.
            # inject_user_context persists the fully prefixed message to DB.
            prefixed_message = await inject_user_context(
                understanding,
                current_message,
                session_id,
                session.messages,
                warm_ctx=warm_ctx,
                env_ctx=env_ctx_content,
            )
            if prefixed_message is not None:
                current_message = prefixed_message

        query_message, was_compacted = await _build_query_message(
            current_message,
            session,
            use_resume,
            transcript_msg_count,
            session_id,
            session_msg_ceiling=_pre_drain_msg_count,
            prior_messages=restore_context_messages,
        )
        # If files are attached, prepare them: images become vision
        # content blocks in the user message, other files go to sdk_cwd.
        attachments = await _prepare_file_attachments(
            file_ids or [], user_id or "", session_id, sdk_cwd
        )
        if attachments.hint:
            query_message = f"{query_message}\n\n{attachments.hint}"

        # warm_ctx is injected via inject_user_context above (warm_ctx= kwarg).
        # No separate injection needed here.

        # Inject per-turn builder context when the session is bound to a
        # graph via ``metadata.builder_graph_id``.  Runs on EVERY user turn
        # (including resumes) so the LLM always sees the live graph snapshot
        # — if the user edits the graph between turns, the next turn carries
        # the updated nodes/links.  The block also carries the full
        # agent-building guide, replacing the per-turn
        # ``get_agent_building_guide`` round-trip.  Not persisted to the
        # transcript: the snapshot is stale-by-definition after the turn ends.
        query_message = await _maybe_prepend_builder_context(
            session, user_id, is_user_message, query_message
        )

        # When running without --resume and no prior transcript in storage,
        # seed the transcript builder from compressed DB messages so that
        # upload_transcript saves a compact version for future turns.
        if not use_resume and not transcript_content and not skip_transcript_upload:
            (
                transcript_content,
                transcript_covers_prefix,
                transcript_msg_count,
            ) = await _seed_transcript(
                session,
                transcript_builder,
                transcript_covers_prefix,
                transcript_msg_count,
                log_prefix,
            )

        tried_compaction = False

        # Build the per-request context carrier (shared across attempts).
        # Scalar fields are immutable; session/compaction/lock are shared
        # mutable references (see `_StreamContext` docstring for details).
        stream_ctx = _StreamContext(
            session=session,
            session_id=session_id,
            log_prefix=log_prefix,
            sdk_cwd=sdk_cwd,
            current_message=current_message,
            file_ids=file_ids,
            message_id=message_id,
            attachments=attachments,
            compaction=compaction,
            lock=lock,
        )

        # ---------------------------------------------------------------
        # Retry loop: original → compacted → no transcript
        # ---------------------------------------------------------------
        ended_with_stream_error = False
        attempts_exhausted = False
        transient_exhausted = False
        stream_err: Exception | None = None

        transient_retries = 0
        max_transient_retries = config.claude_agent_max_transient_retries
        # Preserved across transient retries so the fallback-model notification
        # is not lost when a retry resets local per-attempt variables.  Reset
        # only on context-level attempt changes (same guard as transient_retries).
        fallback_model_activated_per_attempt = False
        fallback_notified_per_attempt = False

        state = _RetryState(
            options=options,
            query_message=query_message,
            was_compacted=was_compacted,
            use_resume=use_resume,
            resume_file=resume_file,
            transcript_msg_count=transcript_msg_count,
            adapter=adapter,
            transcript_builder=transcript_builder,
            usage=_TokenUsage(),
        )

        attempt = 0
        _last_reset_attempt = -1
        while attempt < _MAX_STREAM_ATTEMPTS:
            # Reset transient retry counter per context-level attempt so
            # each attempt (original, compacted, no-transcript) gets the
            # full retry budget for transient errors.
            # Only reset when the attempt number actually changes —
            # transient retries `continue` back to the loop top without
            # incrementing `attempt`, so resetting unconditionally would
            # create an infinite retry loop.
            if attempt != _last_reset_attempt:
                transient_retries = 0
                fallback_model_activated_per_attempt = False
                fallback_notified_per_attempt = False
                _last_reset_attempt = attempt
            # Clear any stale stash signal from the previous attempt so
            # wait_for_stash() doesn't fire prematurely on a leftover event.
            reset_stash_event()
            # Reset tool-level circuit breaker so failures from a previous
            # (rolled-back) attempt don't carry over to the fresh attempt.
            reset_tool_failure_counters()
            if attempt > 0:
                logger.info(
                    "%s Retrying with reduced context (%d/%d)",
                    log_prefix,
                    attempt + 1,
                    _MAX_STREAM_ATTEMPTS,
                )
                yield StreamStatus(message="Optimizing conversation context\u2026")

                ctx = await _reduce_context(
                    transcript_content,
                    tried_compaction,
                    session_id,
                    sdk_cwd,
                    log_prefix,
                    attempt=attempt,
                )
                state.transcript_builder = ctx.builder
                state.use_resume = ctx.use_resume
                state.resume_file = ctx.resume_file
                tried_compaction = ctx.tried_compaction
                state.transcript_msg_count = 0
                state.target_tokens = ctx.target_tokens
                if ctx.transcript_lost:
                    skip_transcript_upload = True

                # Rebuild SDK options and query for the reduced context
                sdk_options_kwargs_retry = dict(sdk_options_kwargs)
                if ctx.use_resume and ctx.resume_file:
                    sdk_options_kwargs_retry["resume"] = ctx.resume_file
                    sdk_options_kwargs_retry.pop("session_id", None)
                elif "session_id" in sdk_options_kwargs:
                    # Initial invocation used session_id (T1 or mode-switch
                    # T1): keep it so the CLI writes the session file to the
                    # predictable path for upload_transcript().  Storage is
                    # ephemeral per invocation, so no "Session ID already in
                    # use" conflict occurs — no prior file was restored.
                    sdk_options_kwargs_retry.pop("resume", None)
                    sdk_options_kwargs_retry["session_id"] = session_id
                else:
                    # T2+ retry without --resume: initial invocation used
                    # --resume, which restored the T1 session file to local
                    # storage.  Re-using session_id without --resume would
                    # fail with "Session ID already in use".
                    sdk_options_kwargs_retry.pop("resume", None)
                    sdk_options_kwargs_retry.pop("session_id", None)
                # Recompute system_prompt for retry — the preset is safe on
                # every turn (requires CLI ≥ 2.1.98, installed in the Docker
                # image and configured via CHAT_CLAUDE_AGENT_CLI_PATH).
                sdk_options_kwargs_retry["system_prompt"] = _build_system_prompt_value(
                    system_prompt,
                    cross_user_cache=config.claude_agent_cross_user_prompt_cache,
                )
                state.options = ClaudeAgentOptions(**sdk_options_kwargs_retry)  # type: ignore[arg-type]  # dynamic kwargs
                # Retry intentionally omits prior_messages (transcript+gap context) and
                # falls back to full session.messages[:-1] from DB — the authoritative
                # source.  transcript+gap is an optimisation for the first attempt only;
                # on retry the extra overhead of full-DB context is acceptable.
                state.query_message, state.was_compacted = await _build_query_message(
                    current_message,
                    session,
                    state.use_resume,
                    state.transcript_msg_count,
                    session_id,
                    session_msg_ceiling=_pre_drain_msg_count,
                    target_tokens=state.target_tokens,
                )
                if attachments.hint:
                    state.query_message = f"{state.query_message}\n\n{attachments.hint}"
                # warm_ctx is already baked into current_message via
                # inject_user_context — no separate injection needed.
                # Re-inject per-turn builder context so retries carry the
                # same live graph snapshot + guide as the initial attempt.
                state.query_message = await _maybe_prepend_builder_context(
                    session, user_id, is_user_message, state.query_message
                )
                state.adapter = SDKResponseAdapter(
                    message_id=message_id,
                    session_id=session_id,
                    render_reasoning_in_ui=config.render_reasoning_in_ui,
                )
                # Reset token accumulators so a failed attempt's partial
                # usage is not double-counted in the successful attempt.
                state.usage.reset()

            pre_attempt_msg_count = len(session.messages)
            # Snapshot transcript builder state — it maintains an
            # independent _entries list from session.messages, so rolling
            # back session.messages alone would leave duplicate entries
            # from the failed attempt in the uploaded transcript.
            transcript_snap = state.transcript_builder.snapshot()
            events_yielded = 0

            try:
                async for event in _run_stream_attempt(stream_ctx, state):
                    if not isinstance(event, _EPHEMERAL_EVENT_TYPES):
                        events_yielded += 1
                    # Emit a one-time StreamStatus when the SDK switches
                    # to the fallback model (detected via stderr).  The flag
                    # is preserved across transient retries (reset only on
                    # context-level attempt change) so the notification is
                    # not lost if the activation occurs during a failed sub-
                    # attempt that later retries successfully.
                    if (
                        fallback_model_activated_per_attempt
                        and not fallback_notified_per_attempt
                    ):
                        fallback_notified_per_attempt = True
                        yield StreamStatus(
                            message="Primary model overloaded — "
                            "using fallback model for this request"
                        )
                    yield event
                break  # Stream completed — exit retry loop
            except asyncio.CancelledError:
                logger.warning(
                    "%s Streaming cancelled (attempt %d/%d)",
                    log_prefix,
                    attempt + 1,
                    _MAX_STREAM_ATTEMPTS,
                )
                raise
            except _HandledStreamError as exc:
                # _run_stream_attempt already yielded a StreamError and
                # appended an error marker.  We only need to rollback
                # session messages and set the error flag — do NOT set
                # stream_err so the post-loop code won't emit a
                # duplicate StreamError.
                session.messages = session.messages[:pre_attempt_msg_count]
                state.transcript_builder.restore(transcript_snap)
                # Check if this is a transient error we can retry with backoff.
                # exc.code is the only reliable signal — str(exc) is always the
                # static "Stream error handled — StreamError already yielded" message.
                if exc.code == "transient_api_error":
                    backoff, transient_retries = _next_transient_backoff(
                        events_yielded, transient_retries, max_transient_retries
                    )
                    if backoff is not None:
                        logger.warning(
                            "%s Transient error — retrying in %ds (%d/%d)",
                            log_prefix,
                            backoff,
                            transient_retries,
                            max_transient_retries,
                        )
                        async for evt in _do_transient_backoff(
                            backoff, state, message_id, session_id
                        ):
                            yield evt
                        continue  # retry the same context-level attempt
                logger.warning(
                    "%s Stream error handled in attempt "
                    "(attempt %d/%d, code=%s, events_yielded=%d)",
                    log_prefix,
                    attempt + 1,
                    _MAX_STREAM_ATTEMPTS,
                    exc.code or "transient",
                    events_yielded,
                )
                # transcript_builder still contains entries from the aborted
                # attempt that no longer match session.messages.  Skip upload
                # so a future --resume doesn't replay rolled-back content.
                skip_transcript_upload = True
                # Re-append the error marker so it survives the rollback
                # and is persisted by the finally block (see #2947655365).
                # Use the specific error message from the attempt (e.g.
                # circuit breaker msg) rather than always the generic one.
                _append_error_marker(
                    session,
                    exc.error_msg or FRIENDLY_TRANSIENT_MSG,
                    retryable=True,
                )
                ended_with_stream_error = True
                # For transient errors the StreamError was deliberately NOT
                # yielded inside _run_stream_attempt (already_yielded=False)
                # so the client didn't see a premature error flash.  Yield it
                # now that we know retries are exhausted.
                # For non-transient errors (circuit breaker, idle timeout)
                # already_yielded=True — do NOT yield again.
                if not exc.already_yielded:
                    yield StreamError(
                        errorText=exc.error_msg or FRIENDLY_TRANSIENT_MSG,
                        code=exc.code or "transient_api_error",
                    )
                break
            except Exception as e:
                stream_err = e
                is_context_error = _is_prompt_too_long(e)
                is_transient = is_transient_api_error(str(e))
                logger.warning(
                    "%s Stream error (attempt %d/%d, context_error=%s, "
                    "transient=%s, events_yielded=%d): %s",
                    log_prefix,
                    attempt + 1,
                    _MAX_STREAM_ATTEMPTS,
                    is_context_error,
                    is_transient,
                    events_yielded,
                    stream_err,
                    exc_info=True,
                )
                session.messages = session.messages[:pre_attempt_msg_count]
                state.transcript_builder.restore(transcript_snap)
                if events_yielded > 0:
                    # Events were already sent to the frontend and cannot be
                    # unsent.  Retrying would produce duplicate/inconsistent
                    # output, so treat this as a final error.
                    logger.warning(
                        "%s Not retrying — %d events already yielded",
                        log_prefix,
                        events_yielded,
                    )
                    skip_transcript_upload = True
                    ended_with_stream_error = True
                    break
                # Transient API errors (ECONNRESET, 429, 5xx) — retry
                # with exponential backoff via the shared helper.
                if is_transient:
                    backoff, transient_retries = _next_transient_backoff(
                        events_yielded, transient_retries, max_transient_retries
                    )
                    if backoff is not None:
                        logger.warning(
                            "%s Transient exception — retrying in %ds (%d/%d)",
                            log_prefix,
                            backoff,
                            transient_retries,
                            max_transient_retries,
                        )
                        async for evt in _do_transient_backoff(
                            backoff, state, message_id, session_id
                        ):
                            yield evt
                        continue  # retry same context-level attempt
                    # Retries exhausted — persist retryable marker so the
                    # frontend shows "Try again" after refresh.
                    # Mirrors the _HandledStreamError exhausted-retry path
                    # at line ~2310.
                    transient_exhausted = True
                    skip_transcript_upload = True
                    _append_error_marker(
                        session, FRIENDLY_TRANSIENT_MSG, retryable=True
                    )
                    ended_with_stream_error = True
                    break

                if not is_context_error:
                    # Non-context, non-transient errors (auth, fatal)
                    # should not trigger compaction — surface immediately.
                    skip_transcript_upload = True
                    ended_with_stream_error = True
                    break
                attempt += 1  # advance to next context-level attempt
                continue
        else:
            # while condition became False — all attempts exhausted without
            # break.  skip_transcript_upload is already set by _reduce_context
            # when the transcript was dropped (transcript_lost=True).
            ended_with_stream_error = True
            attempts_exhausted = True
            logger.error(
                "%s All %d query attempts exhausted: %s",
                log_prefix,
                _MAX_STREAM_ATTEMPTS,
                stream_err,
            )

        if ended_with_stream_error and state is not None:
            # Flush any unresolved tool calls so the frontend can close
            # stale UI elements (e.g. spinners) that were started before
            # the exception interrupted the stream.
            error_flush: list[StreamBaseResponse] = []
            state.adapter._end_text_if_open(error_flush)
            if state.adapter.has_unresolved_tool_calls:
                logger.warning(
                    "%s Flushing %d unresolved tool(s) after stream error",
                    log_prefix,
                    len(state.adapter.current_tool_calls)
                    - len(state.adapter.resolved_tool_calls),
                )
                state.adapter._flush_unresolved_tool_calls(error_flush)
            for response in error_flush:
                yield response

        if ended_with_stream_error and stream_err is not None:
            # Use distinct error codes depending on how the loop ended:
            # • "all_attempts_exhausted" — context compaction ran out of room
            # • "transient_api_error" — 429/5xx/ECONNRESET retries exhausted
            # • "sdk_stream_error" — non-context, non-transient fatal error
            safe_err = str(stream_err).replace("\n", " ").replace("\r", "")[:500]
            if attempts_exhausted:
                error_text = (
                    "Your conversation is too long. "
                    "Please start a new chat or clear some history."
                )
                error_code = "all_attempts_exhausted"
            elif transient_exhausted:
                error_text = FRIENDLY_TRANSIENT_MSG
                error_code = "transient_api_error"
            else:
                error_text = _friendly_error_text(safe_err)
                error_code = "sdk_stream_error"
            yield StreamError(errorText=error_text, code=error_code)

        # Copy token usage from retry state to outer-scope accumulators
        # so the finally block can persist them.
        if state is not None:
            turn_prompt_tokens = state.usage.prompt_tokens
            turn_completion_tokens = state.usage.completion_tokens
            turn_cache_read_tokens = state.usage.cache_read_tokens
            turn_cache_creation_tokens = state.usage.cache_creation_tokens
            turn_cost_usd = state.usage.cost_usd

        # Emit token usage to the client (must be in try to reach SSE stream).
        # Session persistence of usage is in finally to stay consistent with
        # rate-limit recording even if an exception interrupts between here
        # and the finally block.
        if turn_prompt_tokens > 0 or turn_completion_tokens > 0:
            # total_tokens = prompt (uncached input) + completion (output).
            # Cache tokens are tracked separately and excluded from total
            # so that the semantics match the baseline path (OpenRouter)
            # which folds cache into prompt_tokens. Keeping total_tokens
            # = prompt + completion everywhere makes cross-path comparisons
            # and session-level aggregation consistent.
            total_tokens = turn_prompt_tokens + turn_completion_tokens
            yield StreamUsage(
                prompt_tokens=turn_prompt_tokens,
                completion_tokens=turn_completion_tokens,
                total_tokens=total_tokens,
                cache_read_tokens=turn_cache_read_tokens,
                cache_creation_tokens=turn_cache_creation_tokens,
            )

        if ended_with_stream_error:
            logger.warning(
                "%s Stream ended with SDK error after %d messages (compaction=%s)",
                log_prefix,
                len(session.messages),
                compaction.get_log_summary(),
            )
        else:
            logger.info(
                "%s Stream completed successfully with %d messages (compaction=%s)",
                log_prefix,
                len(session.messages),
                compaction.get_log_summary(),
            )
    except GeneratorExit:
        # GeneratorExit is raised when the async generator is closed by the
        # caller (e.g. client disconnect, page refresh).  We MUST release the
        # stream lock here because the ``finally`` block at the end of this
        # function may not execute when GeneratorExit propagates through nested
        # async generators.  Without this, the lock stays held for its full TTL
        # and the user sees "Another stream is already active" on every retry.
        logger.warning("%s GeneratorExit — releasing stream lock", log_prefix)
        await lock.release()
        raise
    except BaseException as e:
        # Catch BaseException to handle both Exception and CancelledError
        # (CancelledError inherits from BaseException in Python 3.8+)
        if isinstance(e, asyncio.CancelledError):
            logger.warning("%s Session cancelled", log_prefix)
            error_msg = "Operation cancelled"
        else:
            error_msg = str(e) or type(e).__name__
            # SDK cleanup errors are expected during client disconnect —
            # log as warning rather than error to reduce Sentry noise.
            # These are normally caught by _safe_close_sdk_client but
            # can escape in edge cases (e.g. GeneratorExit timing).
            if _is_sdk_disconnect_error(e):
                logger.warning(
                    "%s SDK cleanup error (client disconnect): %s",
                    log_prefix,
                    error_msg,
                )
            else:
                logger.error("%s Error: %s", log_prefix, error_msg, exc_info=True)

        is_transient = is_transient_api_error(error_msg)
        if is_transient:
            display_msg, code = FRIENDLY_TRANSIENT_MSG, "transient_api_error"
        else:
            display_msg, code = error_msg, "sdk_error"

        # Append error marker to session (non-invasive text parsing approach).
        # The finally block will persist the session with this error marker.
        # Skip if a marker was already appended inside the stream loop
        # (ended_with_stream_error) to avoid duplicate stale markers.
        if not ended_with_stream_error:
            _append_error_marker(session, display_msg, retryable=is_transient)
            logger.debug(
                "%s Appended error marker, will be persisted in finally",
                log_prefix,
            )

        # Yield StreamError for immediate feedback (only for non-cancellation errors)
        # Skip for CancelledError and SDK disconnect cleanup errors — these
        # are not actionable by the user and the SSE connection is already dead.
        is_cancellation = isinstance(
            e, asyncio.CancelledError
        ) or _is_sdk_disconnect_error(e)
        if not is_cancellation:
            yield StreamError(errorText=display_msg, code=code)

        raise
    finally:
        # Pending messages are drained atomically at the start of each
        # turn (see drain_pending_messages call above), so there's
        # nothing to clean up here — any message pushed after that
        # point belongs to the next turn.

        # --- Close OTEL context (with cost attributes) ---
        if _otel_ctx is not None:
            try:
                span = otel_trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute("gen_ai.usage.prompt_tokens", turn_prompt_tokens)
                    span.set_attribute(
                        "gen_ai.usage.completion_tokens", turn_completion_tokens
                    )
                    span.set_attribute(
                        "gen_ai.usage.cache_read_tokens", turn_cache_read_tokens
                    )
                    span.set_attribute(
                        "gen_ai.usage.cache_creation_tokens",
                        turn_cache_creation_tokens,
                    )
                    if turn_cost_usd is not None:
                        span.set_attribute("gen_ai.usage.cost_usd", turn_cost_usd)
            except Exception:
                logger.debug("Failed to set OTEL cost attributes", exc_info=True)
            try:
                _otel_ctx.__exit__(*sys.exc_info())
            except Exception:
                logger.warning("OTEL context teardown failed", exc_info=True)

        # --- Persist token usage to session + rate-limit counters ---
        # Both must live in finally so they stay consistent even when an
        # exception interrupts the try block after StreamUsage was yielded.
        effective_model = sdk_model or config.thinking_standard_model
        # ``state`` is populated lazily inside the retry loop; when the
        # turn exits before the first attempt runs (e.g. very early
        # validation error) it's still None, so ``generation_ids`` is
        # empty by definition.
        collected_gen_ids: list[str] = (
            list(state.generation_ids) if state is not None else []
        )
        _use_openrouter_reconcile = bool(
            config.openrouter_active
            and config.sdk_reconcile_openrouter_cost
            and collected_gen_ids
        )

        # CLI project dir — used by the reconcile task to sweep for
        # compaction subagents' gen-IDs.  ``sdk_cwd`` is the per-session
        # CLI working directory; the CLI encodes it into the project-dir
        # name the same way ``encode_cwd_for_cli`` does, and writes
        # the main transcript + any ``subagents/`` alongside it under
        # ``~/.claude/projects/<encoded>/``.  Empty when sdk_cwd isn't
        # set (shouldn't happen in practice for SDK turns).
        cli_project_dir: str | None = None
        if sdk_cwd:
            cli_project_dir = os.path.join(
                os.path.expanduser("~/.claude/projects"),
                encode_cwd_for_cli(sdk_cwd),
            )

        if _use_openrouter_reconcile:
            # Defer the single cost-and-rate-limit write to a background
            # task that queries OpenRouter's authoritative
            # ``/generation?id=`` for every round in this turn.  Covers
            # all vendors:
            #
            # * Non-Anthropic (Kimi et al): the CLI's ``total_cost_usd``
            #   is computed from a static Anthropic rate table that
            #   doesn't know the model — silently over-bills by ~5x.
            #   The reconcile replaces it with OpenRouter's real bill.
            # * Anthropic via OpenRouter: the CLI's number matches
            #   Anthropic's own rates penny-for-penny in the common
            #   case, but the reconcile catches any rate change the
            #   CLI binary hasn't picked up and any OpenRouter-side
            #   divergence (cache-discount accounting, promo pricing).
            #
            # The task calls ``persist_and_record_usage`` exactly once
            # per turn — same method as the sync path, so append-only
            # cost-log + rate-limit counter update together.  The sync
            # path below is skipped entirely when the reconcile fires,
            # so no double-counting.  Kill-switch:
            # ``CHAT_SDK_RECONCILE_OPENROUTER_COST=false``.
            #
            # Brief window (~0.5-2s) where the rate-limit counter is
            # unaware of this turn — back-to-back turns in that window
            # see a stale counter.
            asyncio.create_task(
                record_turn_cost_from_openrouter(
                    session=session,
                    user_id=user_id,
                    model=effective_model,
                    prompt_tokens=turn_prompt_tokens,
                    completion_tokens=turn_completion_tokens,
                    cache_read_tokens=turn_cache_read_tokens,
                    cache_creation_tokens=turn_cache_creation_tokens,
                    generation_ids=collected_gen_ids,
                    cli_project_dir=cli_project_dir,
                    cli_session_id=session_id,
                    turn_start_ts=turn_start_ts,
                    fallback_cost_usd=turn_cost_usd,
                    api_key=config.api_key,
                    log_prefix=log_prefix,
                )
            )
        else:
            # Reconcile disabled, OpenRouter inactive, or subscription
            # path (no gen-IDs).  Record the SDK CLI's
            # ``total_cost_usd`` synchronously: accurate for Anthropic
            # (same rate card as billing); for non-Anthropic it's the
            # rate-card estimate that ``_override_cost_for_non_anthropic``
            # caps (still 1.5-2x off vs real OpenRouter bill, but much
            # closer than the ~5x Sonnet-rate fallback).
            await persist_and_record_usage(
                session=session,
                user_id=user_id,
                prompt_tokens=turn_prompt_tokens,
                completion_tokens=turn_completion_tokens,
                cache_read_tokens=turn_cache_read_tokens,
                cache_creation_tokens=turn_cache_creation_tokens,
                log_prefix=log_prefix,
                cost_usd=turn_cost_usd,
                model=effective_model,
                # ``provider`` labels the cost-analytics row; the cost
                # value still comes from the SDK-reported number.
                # Tracks the actual upstream so the row matches reality:
                # OpenRouter when ``openrouter_active``, Anthropic
                # otherwise.
                provider=("open_router" if config.openrouter_active else "anthropic"),
            )

        # --- Persist session messages ---
        # This MUST run in finally to persist messages even when the generator
        # is stopped early (e.g., user clicks stop, processor breaks stream loop).
        # Without this, messages disappear after refresh because they were never
        # saved to the database.
        if session is not None:
            try:
                await asyncio.shield(upsert_chat_session(session))
                logger.info(
                    "%s Session persisted in finally with %d messages",
                    log_prefix,
                    len(session.messages),
                )
            except Exception as persist_err:
                logger.error(
                    "%s Failed to persist session in finally: %s",
                    log_prefix,
                    persist_err,
                    exc_info=True,
                )

        # --- Pause E2B sandbox to stop billing between turns ---
        # Fire-and-forget: pausing is best-effort and must not block the
        # response or the transcript upload.  The task is anchored to
        # _background_tasks to prevent garbage collection.
        # Use pause_sandbox_direct to skip the Redis lookup and reconnect
        # round-trip — e2b_sandbox is the live object from this turn.
        if e2b_sandbox is not None:
            task = asyncio.create_task(pause_sandbox_direct(e2b_sandbox, session_id))
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)

        # --- Graphiti: ingest conversation turn for temporal memory ---
        if graphiti_enabled and user_id and message and is_user_message:
            from ..graphiti.ingest import enqueue_conversation_turn

            # Extract last assistant message from THIS TURN only (not all
            # session history) to avoid distilling stale content from prior
            # turns when the current turn errors before producing output.
            _this_turn_msgs = (
                session.messages[pre_attempt_msg_count:] if session else []
            )
            _assistant_msgs = [
                m.content or "" for m in _this_turn_msgs if m.role == "assistant"
            ]
            _last_assistant = _assistant_msgs[-1] if _assistant_msgs else ""

            _ingest_task = asyncio.create_task(
                enqueue_conversation_turn(
                    user_id, session_id, message, assistant_msg=_last_assistant
                )
            )
            _background_tasks.add(_ingest_task)
            _ingest_task.add_done_callback(_background_tasks.discard)

        # --- Upload CLI native session file for cross-pod --resume ---
        # The CLI writes its native session JSONL after each turn completes.
        # The companion .meta.json carries the message_count watermark and mode
        # so the next turn can restore both --resume context and gap-fill state
        # in a single GCS round-trip via download_transcript().
        # asyncio.shield: if the outer finally-block coroutine is cancelled
        # while awaiting shield, the CancelledError propagates (BaseException,
        # not caught by `except Exception`) letting the caller handle
        # cancellation, while the shielded inner coroutine continues running
        # to completion so the upload is not lost.
        #
        # NOTE: upload is attempted regardless of state.use_resume — even when
        # this turn ran without --resume (restore failed or first T2+ on a new
        # pod), the T1 session file at the expected path may still be present
        # and should be re-uploaded so the next turn can resume from it.
        # read_cli_session_from_disk returns None when the file is absent, so
        # this is always safe.
        #
        # Intentionally NOT gated on skip_transcript_upload: that flag is set
        # when our custom JSONL transcript is dropped (transcript_lost=True on
        # reduced-context retries) but the CLI's native session file is written
        # independently.  Blocking CLI upload on transcript_lost would prevent
        # T1 prompt-too-long retries from uploading their valid session file,
        # breaking --resume on the next pod.  The ended_with_stream_error gate
        # above already covers actual turn failures.
        if (
            config.claude_agent_use_resume
            and user_id
            and sdk_cwd
            and session is not None
            and state is not None
            and not ended_with_stream_error
        ):
            logger.info(
                "%s Attempting CLI session upload"
                " (use_resume=%s, has_history=%s, skip_transcript=%s)",
                log_prefix,
                state.use_resume,
                has_history,
                skip_transcript_upload,
            )
            try:
                # Read the CLI's native session file from disk (written by the CLI
                # after the turn), then upload the bytes to GCS.
                _cli_content = read_cli_session_from_disk(
                    sdk_cwd, session_id, log_prefix
                )
                if _cli_content:
                    # Watermark = number of DB messages this transcript covers.
                    # len(session.messages) is accurate: the CLI session file
                    # was just written after the turn completed, so it covers
                    # all messages through this turn.  Any gap from a prior
                    # missed upload was already detected by detect_gap and
                    # injected as context, so the model has the full history.
                    #
                    # Previously this used _final_tmsg_count + 2, which
                    # under-counted for tool-use turns (delta = 2 + 2*N_tool_calls),
                    # causing persistent spurious gap-fills on every subsequent turn.
                    # That concern was addressed by the inflated-watermark fix
                    # (using the GCS watermark as the anchor for gap detection),
                    # which makes len(session.messages) safe to use here.
                    #
                    # Mid-turn follow-up user rows (persisted via the
                    # StreamToolOutputAvailable handler) are NOT part of the CLI
                    # JSONL — the CLI only knows them as embedded text inside a
                    # tool_result, and even that embedding can be stripped by
                    # the CLI's internal tool_result size cap.  Deduct them
                    # from the watermark so detect_gap on the next turn
                    # treats them as gap-fill entries and the model sees them
                    # as real user messages instead of missing text.
                    _midturn_offset = (
                        state.midturn_user_rows if state is not None else 0
                    )
                    # ``role="reasoning"`` rows are persisted to session.messages
                    # for frontend replay but never appear in the CLI JSONL
                    # (extended_thinking lives embedded in assistant entries, not
                    # as standalone rows).  Exclude them from the watermark so
                    # ``detect_gap`` on the next turn doesn't skip real
                    # user/assistant rows.  See sentry comment 3106186683.
                    _non_reasoning_count = sum(
                        1 for m in session.messages if m.role != "reasoning"
                    )
                    _jsonl_covered = _non_reasoning_count - _midturn_offset
                    await asyncio.shield(
                        upload_transcript(
                            user_id=user_id,
                            session_id=session_id,
                            content=_cli_content,
                            message_count=_jsonl_covered,
                            mode="sdk",
                            log_prefix=log_prefix,
                        )
                    )
            except Exception as cli_upload_err:
                logger.warning(
                    "%s CLI session upload failed in finally: %s",
                    log_prefix,
                    cli_upload_err,
                )

        try:
            if sdk_cwd:
                await _cleanup_sdk_tool_results(sdk_cwd)
        except Exception:
            logger.warning("%s SDK cleanup failed", log_prefix, exc_info=True)
        finally:
            # Release stream lock to allow new streams for this session
            await lock.release()

    # -------------------------------------------------------------------------
    # Auto-continue: drain any messages the user queued AFTER the turn-start
    # drain window and process them as a new turn automatically.
    #
    # This code only executes on NORMAL turn completion.  GeneratorExit and
    # BaseException both re-raise inside their except blocks, so the generator
    # closes before reaching here — messages queued during a cancelled turn are
    # preserved in Redis for the next manual turn.
    # -------------------------------------------------------------------------
    if not ended_with_stream_error:
        _auto_pending_messages = await drain_pending_safe(session_id, log_prefix)
        if _auto_pending_messages:
            logger.info(
                "%s Auto-continuing with %d pending message(s) queued after turn start",
                log_prefix,
                len(_auto_pending_messages),
            )
            # Combine all pending messages into one turn so they are processed
            # together rather than sequentially. The recursive call may itself
            # drain further messages queued while this turn runs.
            _auto_combined = "\n\n".join(pending_texts_from(_auto_pending_messages))
            # Race guard: drain_pending_safe has already LPOPed the messages
            # from Redis. If another request acquires the session lock in the
            # window between our lock.release() above and the recursive call's
            # try_acquire() below, that recursive call exits with
            # "stream_already_active" and the drained messages would be
            # permanently lost. Detect that sentinel on the first yielded
            # event and push the drained messages back to Redis so the
            # competing stream's turn-start drain picks them up — preserving
            # the original ``file_ids`` / ``context`` metadata (sentry
            # r3105523410 — text-only requeue silently stripped it).
            _auto_requeued = False
            _first_auto_event = True

            async def _requeue_drained(reason: str) -> None:
                logger.warning(
                    "%s Auto-continue %s; re-queueing %d drained message(s)",
                    log_prefix,
                    reason,
                    len(_auto_pending_messages),
                )
                for _pm in _auto_pending_messages:
                    try:
                        await push_pending_message(session_id, _pm)
                    except Exception:
                        logger.exception(
                            "%s Failed to re-queue auto-continue message",
                            log_prefix,
                        )

            try:
                async for event in stream_chat_completion_sdk(
                    session_id=session_id,
                    message=_auto_combined,
                    is_user_message=True,
                    user_id=user_id,
                    file_ids=None,
                    permissions=permissions,
                    mode=mode,
                    model=model,
                ):
                    if _first_auto_event:
                        _first_auto_event = False
                        if (
                            isinstance(event, StreamError)
                            and getattr(event, "code", None) == "stream_already_active"
                        ):
                            await _requeue_drained("lost lock race")
                            _auto_requeued = True
                            # Suppress the stale "already active" error —
                            # the competing stream will emit its own events.
                            continue
                    yield event
            except Exception:
                # Eager-persist rollback or any other failure inside the
                # recursive call before messages were consumed. Push the
                # drained texts back so the next turn picks them up.
                if not _auto_requeued:
                    await _requeue_drained("raised during recursive call")
                raise
            if _auto_requeued:
                return