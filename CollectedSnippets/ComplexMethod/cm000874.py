async def test_events_yielded_prevents_retry(self):
        """When events were yielded before a prompt-too-long error, no retry.

        Mid-stream failures after events have been sent cannot be retried
        because the frontend has already rendered partial output.  The
        generator must break immediately with ``sdk_stream_error``.
        """
        import contextlib

        from claude_agent_sdk import AssistantMessage, TextBlock

        from backend.copilot.response_model import StreamError
        from backend.copilot.sdk.service import stream_chat_completion_sdk

        session = self._make_session()
        original_transcript = _build_transcript(
            [("user", "prior question"), ("assistant", "prior answer")]
        )

        # Yield one AssistantMessage with text (produces StreamTextDelta
        # events) then raise prompt-too-long.
        text_msg = AssistantMessage(
            content=[TextBlock(text="partial")],
            model="claude-sonnet-4-20250514",
        )
        prompt_err = Exception("prompt is too long (context_length_exceeded)")
        attempt_count = [0]

        def _client_factory(*a, **kw):
            attempt_count[0] += 1
            return self._make_client_mock_mid_stream_error(
                error=prompt_err,
                pre_error_messages=[text_msg],
            )

        patches = _make_sdk_patches(
            session,
            original_transcript=original_transcript,
            compacted_transcript="compacted",
            client_side_effect=_client_factory,
        )

        events = []
        with contextlib.ExitStack() as stack:
            for target, kwargs in patches:
                stack.enter_context(patch(target, **kwargs))
            async for event in stream_chat_completion_sdk(
                session_id="test-session-id",
                message="hello",
                is_user_message=True,
                user_id="test-user",
                session=session,
            ):
                events.append(event)

        # Should NOT retry — only 1 attempt because events were yielded
        assert attempt_count[0] == 1, (
            f"Expected 1 attempt (no retry after events yielded), "
            f"got {attempt_count[0]}"
        )
        errors = [e for e in events if isinstance(e, StreamError)]
        assert errors, "Expected StreamError"
        assert errors[0].code == "sdk_stream_error"