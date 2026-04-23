async def _run_stream_attempt(
    ctx: _StreamContext,
    state: _RetryState,
) -> AsyncIterator[StreamBaseResponse]:
    """Run one SDK streaming attempt.

    Opens a `ClaudeSDKClient`, sends the query, iterates SDK messages with
    heartbeat timeouts, dispatches adapter responses, and performs post-stream
    cleanup (safety-net flush, stopped-by-user handling).

    Yields stream events.  On stream error the exception propagates to the
    caller so the retry loop can rollback and retry.

    Args:
        ctx: Per-request context shared across retry attempts.  Scalar
            fields (IDs, paths, message string) are set once and never
            reassigned.  `session`, `compaction`, and `lock` are
            shared mutable references: `session.messages` is rolled back
            on retry, `compaction` tracks mid-stream compaction events,
            and `lock` is refreshed during heartbeats.  Their references
            are constant even though the objects they point to are mutated.
        state: Mutable retry state — holds values that the retry loop
            modifies between attempts (options, query, adapter, etc.).

    See also:
        `stream_chat_completion_sdk` — owns the retry loop that calls this
        function up to `_MAX_STREAM_ATTEMPTS` times with reduced context.
    """
    acc = _StreamAccumulator(
        assistant_response=ChatMessage(role="assistant", content=""),
        accumulated_tool_calls=[],
    )
    ended_with_stream_error = False
    # Stores the error message used by _append_error_marker so the outer
    # retry loop can re-append the correct message after session rollback.
    stream_error_msg: str | None = None
    stream_error_code: str | None = None

    consecutive_empty_tool_calls = 0

    # --- Intermediate persistence tracking ---
    # Flush session messages to DB periodically so page reloads show progress
    # during long-running turns (see incident d2f7cba3: 82-min turn lost on refresh).
    _last_flush_time = time.monotonic()
    _msgs_since_flush = 0
    _FLUSH_INTERVAL_SECONDS = 30.0
    _FLUSH_MESSAGE_THRESHOLD = 10

    # Use manual __aenter__/__aexit__ instead of ``async with`` so we can
    # suppress SDK cleanup errors that occur when the SSE client disconnects
    # mid-stream.  GeneratorExit causes the SDK's ``__aexit__`` to run in a
    # different async context/task than where the client was opened, which
    # triggers:
    #   - ValueError: ContextVar token mismatch (AUTOGPT-SERVER-8BT)
    #   - RuntimeError: cancel scope in wrong task  (AUTOGPT-SERVER-8BW)
    # Both are harmless — the TCP connection is already dead.
    sdk_client = ClaudeSDKClient(options=state.options)
    client = await sdk_client.__aenter__()
    try:
        logger.info(
            "%s Sending query — resume=%s, total_msgs=%d, "
            "query_len=%d, attached_files=%d, image_blocks=%d",
            ctx.log_prefix,
            state.use_resume,
            len(ctx.session.messages),
            len(state.query_message),
            len(ctx.file_ids) if ctx.file_ids else 0,
            len(ctx.attachments.image_blocks),
        )

        ctx.compaction.reset_for_query()
        if state.was_compacted:
            for ev in ctx.compaction.emit_pre_query(ctx.session):
                yield ev

        if ctx.attachments.image_blocks:
            content_blocks: list[dict[str, Any]] = [
                *ctx.attachments.image_blocks,
                {"type": "text", "text": state.query_message},
            ]
            user_msg = {
                "type": "user",
                "message": {"role": "user", "content": content_blocks},
                "parent_tool_use_id": None,
                "session_id": ctx.session_id,
            }
            if client._transport is None:  # noqa: SLF001
                raise RuntimeError("ClaudeSDKClient transport is not initialized")
            await client._transport.write(json.dumps(user_msg) + "\n")  # noqa: SLF001
            state.transcript_builder.append_user(
                content=[
                    *ctx.attachments.image_blocks,
                    {"type": "text", "text": ctx.current_message},
                ]
            )
        else:
            await client.query(state.query_message, session_id=ctx.session_id)
            state.transcript_builder.append_user(content=ctx.current_message)

        _last_real_msg_time = time.monotonic()

        async for sdk_msg in _iter_sdk_messages(client):
            # Heartbeat sentinel — refresh lock and keep SSE alive
            if sdk_msg is None:
                await ctx.lock.refresh()
                for ev in ctx.compaction.emit_start_if_ready():
                    yield ev
                yield StreamHeartbeat()

                # Idle timeout: abort if the SDK has been silent for too long.
                # Long-running tools use the async "start + poll" pattern so
                # the MCP handler never blocks longer than the poll cap (5 min)
                # — a 10-min gap here means the SDK itself is stuck.
                idle_seconds = time.monotonic() - _last_real_msg_time
                if idle_seconds >= _IDLE_TIMEOUT_SECONDS:
                    logger.error(
                        "%s Idle timeout after %.0fs — aborting stream",
                        ctx.log_prefix,
                        idle_seconds,
                    )
                    stream_error_msg = (
                        "The session has been idle for too long. Please try again."
                    )
                    stream_error_code = "idle_timeout"
                    _append_error_marker(ctx.session, stream_error_msg, retryable=True)
                    yield StreamError(
                        errorText=stream_error_msg,
                        code=stream_error_code,
                    )
                    ended_with_stream_error = True
                    break
                continue

            _last_real_msg_time = time.monotonic()

            logger.info(
                "%s Received: %s %s (unresolved=%d, current=%d, resolved=%d)",
                ctx.log_prefix,
                type(sdk_msg).__name__,
                getattr(sdk_msg, "subtype", ""),
                len(state.adapter.current_tool_calls)
                - len(state.adapter.resolved_tool_calls),
                len(state.adapter.current_tool_calls),
                len(state.adapter.resolved_tool_calls),
            )

            # Capture OpenRouter generation IDs from each
            # ``AssistantMessage.message_id`` — when routed via OpenRouter
            # these are ``gen-...`` slugs we can use post-turn to query
            # ``/api/v1/generation?id=`` for the authoritative per-turn
            # cost and token counts (the CLI's ``total_cost_usd`` is
            # computed from a static Anthropic pricing table that
            # silently over-bills non-Anthropic routes).  Direct-Anthropic
            # turns produce ``msg_...`` IDs which the generation endpoint
            # doesn't know about — harmlessly ignored at reconcile time.
            if isinstance(sdk_msg, AssistantMessage):
                msg_id = sdk_msg.message_id
                if (
                    msg_id is not None
                    and msg_id.startswith("gen-")
                    and msg_id not in state.generation_ids
                ):
                    state.generation_ids.append(msg_id)
                # Track the model the SDK actually used — when a fallback
                # activates, this differs from ``state.options.model``.
                # Consumed by the Moonshot cost-override decision so we
                # don't mis-bill a fallback-Anthropic response at
                # Moonshot rates (or a fallback-Moonshot at Anthropic
                # rates).
                observed = getattr(sdk_msg, "model", None)
                if isinstance(observed, str) and observed:
                    state.observed_model = observed

            # Log AssistantMessage API errors (e.g. invalid_request)
            # so we can debug Anthropic API 400s surfaced by the CLI.
            sdk_error = getattr(sdk_msg, "error", None)
            if isinstance(sdk_msg, AssistantMessage) and sdk_error:
                error_text = str(sdk_error)
                error_preview = str(sdk_msg.content)[:500]
                logger.error(
                    "[SDK] [%s] AssistantMessage has error=%s, "
                    "content_blocks=%d, content_preview=%s",
                    ctx.session_id[:12],
                    sdk_error,
                    len(sdk_msg.content),
                    error_preview,
                )

                # Intercept prompt-too-long errors surfaced as
                # AssistantMessage.error (not as a Python exception).
                # Re-raise so the outer retry loop can compact the
                # transcript and retry with reduced context.
                # Check both error_text and error_preview: sdk_error
                # being set confirms this is an error message (not user
                # content), so checking content is safe. The actual
                # error description (e.g. "Prompt is too long") may be
                # in the content, not the error type field
                # (e.g. error="invalid_request", content="Prompt is
                # too long").
                if _is_prompt_too_long(Exception(error_text)) or _is_prompt_too_long(
                    Exception(error_preview)
                ):
                    logger.warning(
                        "%s Prompt-too-long detected via AssistantMessage "
                        "error — raising for retry",
                        ctx.log_prefix,
                    )
                    raise RuntimeError("Prompt is too long")

                # Intercept transient API errors (socket closed,
                # ECONNRESET) — replace the raw message with a
                # user-friendly error text and use the retryable
                # error prefix so the frontend shows a retry button.
                # Check both the error field and content for patterns.
                if is_transient_api_error(error_text) or is_transient_api_error(
                    error_preview
                ):
                    logger.warning(
                        "%s Transient Anthropic API error detected, "
                        "suppressing raw error text",
                        ctx.log_prefix,
                    )
                    stream_error_msg = FRIENDLY_TRANSIENT_MSG
                    stream_error_code = "transient_api_error"
                    # Do NOT yield StreamError or append error marker here.
                    # The outer retry loop decides: if a retry is available it
                    # yields StreamStatus("retrying…"); if retries are exhausted
                    # it appends the marker and yields StreamError exactly once.
                    # Yielding StreamError before the retry decision causes the
                    # client to display an error that is immediately superseded.
                    ended_with_stream_error = True
                    break

            # Determine if the message is a tool-only batch (all content
            # items are ToolUseBlocks) — such messages have no text output yet,
            # so we skip the wait_for_stash flush below.
            #
            # Note: parallel execution of tools is handled natively by the
            # SDK CLI via readOnlyHint annotations on tool definitions.
            is_tool_only = False
            if isinstance(sdk_msg, AssistantMessage) and sdk_msg.content:
                is_tool_only = all(
                    isinstance(item, ToolUseBlock) for item in sdk_msg.content
                )

            # Race-condition fix: SDK hooks (PostToolUse) are
            # executed asynchronously via start_soon() — the next
            # message can arrive before the hook stashes output.
            # wait_for_stash() awaits an asyncio.Event signaled by
            # stash_pending_tool_output(), completing as soon as
            # the hook finishes (typically <1ms).  The sleep(0)
            # after lets any remaining concurrent hooks complete.
            #
            # Skip for parallel tool continuations: when the SDK
            # sends parallel tool calls as separate
            # AssistantMessages (each containing only
            # ToolUseBlocks), we must NOT wait/flush — the prior
            # tools are still executing concurrently.
            if (
                state.adapter.has_unresolved_tool_calls
                and isinstance(sdk_msg, (AssistantMessage, ResultMessage))
                and not is_tool_only
            ):
                if await wait_for_stash():
                    await asyncio.sleep(0)
                else:
                    logger.warning(
                        "%s Timed out waiting for PostToolUse "
                        "hook stash (%d unresolved tool calls)",
                        ctx.log_prefix,
                        len(state.adapter.current_tool_calls)
                        - len(state.adapter.resolved_tool_calls),
                    )

            # Log ResultMessage details and capture token usage
            if isinstance(sdk_msg, ResultMessage):
                logger.info(
                    "%s Received: ResultMessage %s "
                    "(unresolved=%d, current=%d, resolved=%d, "
                    "num_turns=%d, cost_usd=%s, result=%s)",
                    ctx.log_prefix,
                    sdk_msg.subtype,
                    len(state.adapter.current_tool_calls)
                    - len(state.adapter.resolved_tool_calls),
                    len(state.adapter.current_tool_calls),
                    len(state.adapter.resolved_tool_calls),
                    sdk_msg.num_turns,
                    sdk_msg.total_cost_usd,
                    (sdk_msg.result or "")[:200],
                )
                if sdk_msg.subtype in (
                    "error",
                    "error_during_execution",
                ):
                    logger.error(
                        "%s SDK execution failed with error: %s",
                        ctx.log_prefix,
                        sdk_msg.result or "(no error message provided)",
                    )

                # Check for prompt-too-long regardless of subtype — the
                # SDK may return subtype="success" with result="Prompt is
                # too long" when the CLI rejects the prompt before calling
                # the API (cost_usd=0, no tokens consumed).  If we only
                # check the "error" subtype path, the stream appears to
                # complete normally, the synthetic error text is stored
                # in the transcript, and the session grows without bound.
                if _is_prompt_too_long(RuntimeError(sdk_msg.result or "")):
                    raise RuntimeError("Prompt is too long")

                # Capture token usage from ResultMessage.
                # Anthropic reports cached tokens separately:
                #   input_tokens = uncached only
                #   cache_read_input_tokens = served from cache
                #   cache_creation_input_tokens = written to cache
                if sdk_msg.usage:
                    # Use `or 0` instead of a default in .get() because
                    # OpenRouter may include the key with a null value (e.g.
                    # {"cache_read_input_tokens": null}) for models that don't
                    # yet report cache tokens, making .get("key", 0) return
                    # None rather than the fallback 0.
                    state.usage.prompt_tokens += sdk_msg.usage.get("input_tokens") or 0
                    state.usage.cache_read_tokens += (
                        sdk_msg.usage.get("cache_read_input_tokens") or 0
                    )
                    state.usage.cache_creation_tokens += (
                        sdk_msg.usage.get("cache_creation_input_tokens") or 0
                    )
                    state.usage.completion_tokens += (
                        sdk_msg.usage.get("output_tokens") or 0
                    )
                    logger.info(
                        "%s Token usage: uncached=%d, cache_read=%d, "
                        "cache_create=%d, output=%d",
                        ctx.log_prefix,
                        state.usage.prompt_tokens,
                        state.usage.cache_read_tokens,
                        state.usage.cache_creation_tokens,
                        state.usage.completion_tokens,
                    )
                if sdk_msg.total_cost_usd is not None:
                    # Default: trust the CLI-reported value.  Accurate for
                    # Anthropic models (the CLI's bundled pricing table is
                    # Anthropic-authored), and becomes the sync-path cost
                    # when the reconcile is disabled or fails.
                    # Prefer the ACTUALLY executed model
                    # (``state.observed_model`` from ``AssistantMessage.model``)
                    # over the requested primary (``state.options.model``)
                    # so a fallback activation doesn't mis-route pricing.
                    active_model = state.observed_model or getattr(
                        state.options, "model", None
                    )
                    if _is_moonshot_model(active_model):
                        # Moonshot slug — the CLI doesn't know Moonshot's
                        # rate card and silently bills at Sonnet rates
                        # (~5x over-charge).  Replace with the rate-card
                        # estimate so the in-stream ``cost_usd`` and the
                        # reconcile's lookup-fail fallback reflect
                        # reality.  Reconcile
                        # (``record_turn_cost_from_openrouter``) still
                        # overrides this value when every gen-ID lookup
                        # succeeds.
                        state.usage.cost_usd = _override_cost_for_moonshot(
                            model=active_model,
                            sdk_reported_usd=sdk_msg.total_cost_usd,
                            prompt_tokens=state.usage.prompt_tokens,
                            completion_tokens=state.usage.completion_tokens,
                            cache_read_tokens=state.usage.cache_read_tokens,
                            cache_creation_tokens=state.usage.cache_creation_tokens,
                        )
                    else:
                        state.usage.cost_usd = sdk_msg.total_cost_usd

            # Emit compaction end if SDK finished compacting.
            # Sync TranscriptBuilder with the CLI's active context.
            compact_result = await ctx.compaction.emit_end_if_ready(ctx.session)
            if compact_result.events:
                # Compaction events end with StreamFinishStep, which maps to
                # Vercel AI SDK's "finish-step" — that clears activeTextParts.
                # Close any open text block BEFORE the compaction events so
                # the text-end arrives before finish-step, preventing
                # "text-end for missing text part" errors on the frontend.
                pre_close: list[StreamBaseResponse] = []
                state.adapter._end_text_if_open(pre_close)
                # Compaction events bypass the adapter, so sync step state
                # when a StreamFinishStep is present — otherwise the adapter
                # will skip StreamStartStep on the next AssistantMessage.
                if any(
                    isinstance(ev, StreamFinishStep) for ev in compact_result.events
                ):
                    state.adapter.step_open = False
                for r in pre_close:
                    yield r
            for ev in compact_result.events:
                yield ev
            entries_replaced = False
            if compact_result.just_ended:
                compacted = await asyncio.to_thread(
                    read_compacted_entries,
                    compact_result.transcript_path,
                )
                if compacted is not None:
                    state.transcript_builder.replace_entries(
                        compacted, log_prefix=ctx.log_prefix
                    )
                    entries_replaced = True

            # --- Hard circuit breaker for empty tool calls ---
            breaker = _check_empty_tool_breaker(
                sdk_msg, consecutive_empty_tool_calls, ctx, state
            )
            consecutive_empty_tool_calls = breaker.count
            if breaker.tripped and breaker.error is not None:
                stream_error_msg = breaker.error_msg
                stream_error_code = breaker.error_code
                yield breaker.error
                ended_with_stream_error = True
                break

            # --- Dispatch adapter responses ---
            adapter_responses = state.adapter.convert_message(sdk_msg)

            # Pre-create the new assistant message in the session BEFORE
            # yielding any events so it survives a GeneratorExit (client
            # disconnect) that interrupts the yield loop at StreamStartStep.
            #
            # Without this, the sequence is:
            #   tool result saved → intermediate flush → StreamStartStep
            #   yield → GeneratorExit → finally saves session with
            #   last_role=tool (the text response was generated but never
            #   appended because _dispatch_response(StreamTextDelta) was
            #   skipped).
            #
            # We only pre-create when:
            #   1. Tool results were received this turn (has_tool_results).
            #   2. The prior assistant message is already appended
            #      (has_appended_assistant) — so this is a post-tool turn.
            #   3. This batch contains StreamTextDelta — text IS coming, so
            #      we won't leave a spurious empty message for tool-only turns.
            #
            # Subsequent StreamTextDelta dispatches accumulate content into
            # acc.assistant_response in-place (ChatMessage is mutable), so
            # the DB record is updated without a second append.
            if (
                acc.has_tool_results
                and acc.has_appended_assistant
                and any(isinstance(r, StreamTextDelta) for r in adapter_responses)
            ):
                acc.assistant_response = ChatMessage(role="assistant", content="")
                acc.accumulated_tool_calls = []
                acc.has_tool_results = False
                ctx.session.messages.append(acc.assistant_response)
                # acc.has_appended_assistant stays True — placeholder is live

            # When StreamFinish is in this batch (ResultMessage), flush any
            # text buffered by the thinking stripper and inject it as a
            # StreamTextDelta BEFORE the StreamTextEnd so the Vercel AI SDK
            # receives the tail inside the still-open text block (correct
            # protocol order: TextDelta → TextEnd → FinishStep → Finish).
            tail_delta: StreamTextDelta | None = None
            if any(isinstance(r, StreamFinish) for r in adapter_responses):
                tail = acc.thinking_stripper.flush()
                if tail and not ended_with_stream_error:
                    # Do NOT manually append tail to acc.assistant_response.content
                    # here — _dispatch_response handles that.  Doing it here would
                    # double-append because _dispatch_response also updates the
                    # accumulator.  Instead, mark the delta as pre-stripped so
                    # _dispatch_response bypasses ThinkingStripper.process() for it
                    # (re-processing could suppress a tail that looks like a partial
                    # tag opener, e.g. "Hello <inter" → buffered again → lost).
                    tail_delta = StreamTextDelta(
                        id=state.adapter.text_block_id, delta=tail
                    )
                    insert_at = next(
                        (
                            i
                            for i, r in enumerate(adapter_responses)
                            if isinstance(r, (StreamTextEnd, StreamFinish))
                        ),
                        len(adapter_responses),
                    )
                    adapter_responses.insert(insert_at, tail_delta)
            for response in adapter_responses:
                dispatched = _dispatch_response(
                    response,
                    acc,
                    ctx,
                    state,
                    entries_replaced,
                    ctx.log_prefix,
                    skip_strip=response is tail_delta,
                )
                if dispatched is not None:
                    # Persistence (via _dispatch_response) always runs so the
                    # session transcript keeps role='reasoning' rows; the
                    # wire is gated so UI can suppress rendering.
                    if not state.adapter.render_reasoning_in_ui and isinstance(
                        dispatched,
                        (
                            StreamReasoningStart,
                            StreamReasoningDelta,
                            StreamReasoningEnd,
                        ),
                    ):
                        continue
                    yield dispatched

                # Mid-turn follow-up persistence: the MCP tool wrapper drains
                # the primary pending buffer and stashes the drained
                # PendingMessages into the per-session persist queue.  Claude
                # has already seen them via the <user_follow_up> block
                # injected into the tool output.  Now — right after the
                # tool_result row has been appended to session.messages — we
                # pop the persist queue and append a real user ChatMessage
                # so the UI renders a proper user bubble in the correct
                # chronological position (after the tool_result, before the
                # assistant's continuing response).  Rollback re-queues into
                # the PRIMARY pending buffer so the next turn-start drain
                # picks them up if this persist silently fails.
                # Only run the follow-up persist if the tool_result row was
                # actually appended by _dispatch_response (currently always
                # true for this variant, but we guard so a future refactor
                # that conditionally skips the append can't silently land
                # a user row before a missing tool_result).
                if (
                    isinstance(response, StreamToolOutputAvailable)
                    and dispatched is not None
                    and acc.has_tool_results
                ):
                    followup_drained = await drain_pending_for_persist(
                        ctx.session.session_id
                    )
                    if followup_drained and await persist_pending_as_user_rows(
                        ctx.session,
                        state.transcript_builder,
                        followup_drained,
                        log_prefix=ctx.log_prefix,
                    ):
                        # Track CLI-JSONL-invisible rows so the upload
                        # watermark excludes them and the next turn's
                        # detect_gap picks them up as gap-fill.
                        state.midturn_user_rows += len(followup_drained)

            # Append assistant entry AFTER convert_message so that
            # any stashed tool results from the previous turn are
            # recorded first, preserving the required API order:
            # assistant(tool_use) → tool_result → assistant(text).
            # Skip if replace_entries just ran — the CLI session
            # file already contains this message.
            if isinstance(sdk_msg, AssistantMessage) and not entries_replaced:
                state.transcript_builder.append_assistant(
                    content_blocks=_format_sdk_content_blocks(sdk_msg.content),
                    model=sdk_msg.model,
                )

            # --- Intermediate persistence ---
            # Flush session messages to DB periodically so page reloads
            # show progress during long-running turns.
            #
            # IMPORTANT: Skip the flush while tool calls are pending
            # (tool_calls set on assistant but results not yet received).
            # The DB save is append-only (uses start_sequence), so if we
            # flush the assistant message before tool_calls are set on it
            # (text and tool_use arrive as separate SDK events), the
            # tool_calls update is lost — the next flush starts past it.
            #
            # With ``include_partial_messages=True`` the CLI delivers
            # hundreds of ``StreamEvent`` messages per turn — incrementing
            # ``_msgs_since_flush`` on each one trips the threshold long
            # before the assistant text is complete, saving a truncated
            # prefix that subsequent deltas can never extend (append-only).
            # Count only messages that produce a persisted row boundary
            # (AssistantMessage, UserMessage, ResultMessage) and skip
            # raw StreamEvents.  Also skip when text or reasoning is
            # still in-flight on the adapter: the row is live and a flush
            # would lock it at its current length.
            if not isinstance(sdk_msg, StreamEvent):
                _msgs_since_flush += 1
            now = time.monotonic()
            has_pending_tools = (
                acc.has_appended_assistant
                and acc.accumulated_tool_calls
                and not acc.has_tool_results
            )
            adapter = state.adapter
            has_open_block = (
                adapter.has_started_text and not adapter.has_ended_text
            ) or (adapter.has_started_reasoning and not adapter.has_ended_reasoning)
            if (
                not has_pending_tools
                and not has_open_block
                and (
                    _msgs_since_flush >= _FLUSH_MESSAGE_THRESHOLD
                    or (now - _last_flush_time) >= _FLUSH_INTERVAL_SECONDS
                )
            ):
                try:
                    await asyncio.shield(upsert_chat_session(ctx.session))
                    logger.debug(
                        "%s Intermediate flush: %d messages "
                        "(msgs_since=%d, elapsed=%.1fs)",
                        ctx.log_prefix,
                        len(ctx.session.messages),
                        _msgs_since_flush,
                        now - _last_flush_time,
                    )
                except Exception as flush_err:
                    logger.warning(
                        "%s Intermediate flush failed: %s",
                        ctx.log_prefix,
                        flush_err,
                    )
                _last_flush_time = now
                _msgs_since_flush = 0

            if acc.stream_completed:
                break
    finally:
        await _safe_close_sdk_client(sdk_client, ctx.log_prefix)

    # --- Post-stream processing (only on success) ---
    if state.adapter.has_unresolved_tool_calls:
        logger.warning(
            "%s %d unresolved tool(s) after stream — flushing",
            ctx.log_prefix,
            len(state.adapter.current_tool_calls)
            - len(state.adapter.resolved_tool_calls),
        )
        safety_responses: list[StreamBaseResponse] = []
        state.adapter._flush_unresolved_tool_calls(safety_responses)
        for response in safety_responses:
            if isinstance(
                response,
                (StreamToolInputAvailable, StreamToolOutputAvailable),
            ):
                logger.info(
                    "%s Safety flush: %s, tool=%s",
                    ctx.log_prefix,
                    type(response).__name__,
                    getattr(response, "toolName", "N/A"),
                )
            if isinstance(response, StreamToolOutputAvailable):
                state.transcript_builder.append_tool_result(
                    tool_use_id=response.toolCallId,
                    content=(
                        response.output
                        if isinstance(response.output, str)
                        else json.dumps(response.output, ensure_ascii=False)
                    ),
                )
            yield response

    if not acc.stream_completed and not ended_with_stream_error:
        logger.info(
            "%s Stream ended without ResultMessage (stopped by user)",
            ctx.log_prefix,
        )
        closing_responses: list[StreamBaseResponse] = []
        state.adapter._end_text_if_open(closing_responses)
        for r in closing_responses:
            yield r
        ctx.session.messages.append(
            ChatMessage(role="assistant", content=STOPPED_BY_USER_MARKER)
        )

    if (
        acc.assistant_response.content or acc.assistant_response.tool_calls
    ) and not acc.has_appended_assistant:
        ctx.session.messages.append(acc.assistant_response)

    # Raise so the outer retry loop can rollback session messages.
    # already_yielded=False for transient_api_error: StreamError was NOT
    # sent to the client yet (the outer loop does it when retries are
    # exhausted, avoiding a premature error flash before the retry).
    if ended_with_stream_error:
        raise _HandledStreamError(
            "Stream error handled",
            error_msg=stream_error_msg,
            code=stream_error_code,
            already_yielded=(stream_error_code != "transient_api_error"),
        )