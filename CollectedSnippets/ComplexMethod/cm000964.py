def test_flushed_assistant_text_len_prevents_duplicate_final_text(self):
        """After mid-loop drain clears state.session_messages, the finally
        block must not re-append assistant text from rounds already flushed.

        ``state.assistant_text`` accumulates ALL rounds' text, but
        ``state.session_messages`` only holds entries from rounds AFTER the
        last mid-loop flush.  Without ``_flushed_assistant_text_len``, the
        ``finally`` block's ``startswith(recorded)`` check fails because
        ``recorded`` only covers post-flush rounds, and the full
        ``assistant_text`` is appended — duplicating pre-flush rounds.
        """
        state = _BaselineStreamState()
        session_messages: list[ChatMessage] = [
            ChatMessage(role="user", content="user turn"),
        ]

        # Simulate round 1 text accumulation (as _bound_llm_caller does)
        state.assistant_text += "calling search"

        # Round 1 conversation_updater buffers structured entries
        builder = TranscriptBuilder()
        builder.append_user("user turn")
        response1 = LLMLoopResponse(
            response_text="calling search",
            tool_calls=[LLMToolCall(id="tc_1", name="search", arguments="{}")],
            raw_response=None,
            prompt_tokens=0,
            completion_tokens=0,
        )
        _baseline_conversation_updater(
            [],
            response1,
            tool_results=[
                ToolCallResult(
                    tool_call_id="tc_1", tool_name="search", content="result"
                )
            ],
            transcript_builder=builder,
            state=state,
            model="test-model",
        )

        # Mid-loop drain: flush + clear + record flushed text length
        for _buffered in state.session_messages:
            session_messages.append(_buffered)
        state.session_messages.clear()
        state._flushed_assistant_text_len = len(state.assistant_text)
        session_messages.append(ChatMessage(role="user", content="pending message"))

        # Simulate round 2 text accumulation
        state.assistant_text += "final answer"

        # Round 2: natural finish (no tool calls → no session_messages entry)

        # --- Finally block logic (production code) ---
        for msg in state.session_messages:
            session_messages.append(msg)

        final_text = state.assistant_text[state._flushed_assistant_text_len :]
        if state.session_messages:
            recorded = "".join(
                m.content or "" for m in state.session_messages if m.role == "assistant"
            )
            if final_text.startswith(recorded):
                final_text = final_text[len(recorded) :]
        if final_text.strip():
            session_messages.append(ChatMessage(role="assistant", content=final_text))

        # The final assistant message should only contain round-2 text,
        # not the round-1 text that was already flushed mid-loop.
        assistant_msgs = [m for m in session_messages if m.role == "assistant"]
        # Round-1 structured assistant (from mid-loop flush)
        assert assistant_msgs[0].content == "calling search"
        assert assistant_msgs[0].tool_calls is not None
        # Round-2 final text (from finally block)
        assert assistant_msgs[1].content == "final answer"
        assert assistant_msgs[1].tool_calls is None
        # Crucially: only 2 assistant messages, not 3 (no duplicate)
        assert len(assistant_msgs) == 2