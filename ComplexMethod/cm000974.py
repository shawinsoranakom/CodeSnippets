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