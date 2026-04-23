async def test_result_message_prompt_too_long_triggers_compaction(self):
        """CLI returns ResultMessage(subtype="error") with "Prompt is too long".

        When the Claude CLI rejects the prompt pre-API (model=<synthetic>,
        duration_api_ms=0), it sends a ResultMessage with is_error=True
        instead of raising a Python exception.  The retry loop must still
        detect this as a context-length error and trigger compaction.
        """
        import contextlib

        from claude_agent_sdk import ResultMessage

        from backend.copilot.response_model import StreamError, StreamStart
        from backend.copilot.sdk.service import stream_chat_completion_sdk

        session = self._make_session()
        success_result = self._make_result_message()
        attempt_count = [0]

        error_result = ResultMessage(
            subtype="error",
            result="Prompt is too long",
            duration_ms=100,
            duration_api_ms=0,
            is_error=True,
            num_turns=0,
            session_id="test-session-id",
        )

        def _client_factory(*args, **kwargs):
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                # First attempt: CLI returns error ResultMessage
                return self._make_client_mock(result_message=error_result)
            # Second attempt (after compaction): succeeds
            return self._make_client_mock(result_message=success_result)

        original_transcript = _build_transcript(
            [("user", "prior question"), ("assistant", "prior answer")]
        )
        compacted_transcript = _build_transcript(
            [("user", "[summary]"), ("assistant", "summary reply")]
        )

        patches = _make_sdk_patches(
            session,
            original_transcript=original_transcript,
            compacted_transcript=compacted_transcript,
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

        assert attempt_count[0] == 2, (
            f"Expected 2 SDK attempts (CLI error ResultMessage "
            f"should trigger compaction retry), got {attempt_count[0]}"
        )
        errors = [e for e in events if isinstance(e, StreamError)]
        assert not errors, f"Unexpected StreamError: {errors}"
        assert any(isinstance(e, StreamStart) for e in events)