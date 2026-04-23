def test_flush_then_append_preserves_chronological_order(self):
        """Mid-loop drain must flush state.session_messages before appending
        the pending user message, so the final order matches the
        chronological execution order.
        """
        # Initial state: user turn already appended by maybe_append_user_message
        session_messages: list[ChatMessage] = [
            ChatMessage(role="user", content="original user turn"),
        ]
        state = _BaselineStreamState()

        # Round 1 completes: conversation_updater buffers assistant+tool
        # entries into state.session_messages (but does NOT write to
        # session.messages yet).
        builder = TranscriptBuilder()
        builder.append_user("original user turn")
        response = LLMLoopResponse(
            response_text="calling search",
            tool_calls=[LLMToolCall(id="tc_1", name="search", arguments="{}")],
            raw_response=None,
            prompt_tokens=0,
            completion_tokens=0,
        )
        tool_results = [
            ToolCallResult(
                tool_call_id="tc_1", tool_name="search", content="search output"
            ),
        ]
        openai_messages: list = []
        _baseline_conversation_updater(
            openai_messages,
            response,
            tool_results=tool_results,
            transcript_builder=builder,
            state=state,
            model="test-model",
        )
        # state.session_messages should now hold the round-1 assistant + tool
        assert len(state.session_messages) == 2
        assert state.session_messages[0].role == "assistant"
        assert state.session_messages[1].role == "tool"

        # --- Mid-loop pending drain (production code pattern) ---
        # Flush first, THEN append pending.  This is the ordering fix.
        for _buffered in state.session_messages:
            session_messages.append(_buffered)
        state.session_messages.clear()
        session_messages.append(
            ChatMessage(role="user", content="pending mid-loop message")
        )

        # Round 2 completes: new assistant+tool entries buffer again.
        response2 = LLMLoopResponse(
            response_text="another call",
            tool_calls=[LLMToolCall(id="tc_2", name="calc", arguments="{}")],
            raw_response=None,
            prompt_tokens=0,
            completion_tokens=0,
        )
        tool_results2 = [
            ToolCallResult(
                tool_call_id="tc_2", tool_name="calc", content="calc output"
            ),
        ]
        _baseline_conversation_updater(
            openai_messages,
            response2,
            tool_results=tool_results2,
            transcript_builder=builder,
            state=state,
            model="test-model",
        )

        # --- Finally-block flush (end of turn) ---
        for msg in state.session_messages:
            session_messages.append(msg)

        # Assert chronological order: original user, round-1 assistant,
        # round-1 tool, pending user, round-2 assistant, round-2 tool.
        assert [m.role for m in session_messages] == [
            "user",
            "assistant",
            "tool",
            "user",
            "assistant",
            "tool",
        ]
        assert session_messages[0].content == "original user turn"
        assert session_messages[3].content == "pending mid-loop message"
        # The assistant message carrying tool_call tc_1 must be immediately
        # followed by its tool result — no user message interposed.
        assert session_messages[1].role == "assistant"
        assert session_messages[1].tool_calls is not None
        assert session_messages[1].tool_calls[0]["id"] == "tc_1"
        assert session_messages[2].role == "tool"
        assert session_messages[2].tool_call_id == "tc_1"
        # Same invariant for the round after the pending user.
        assert session_messages[4].tool_calls is not None
        assert session_messages[4].tool_calls[0]["id"] == "tc_2"
        assert session_messages[5].tool_call_id == "tc_2"