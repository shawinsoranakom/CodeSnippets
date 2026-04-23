async def test_prompt_too_long_retries_with_compaction(self):
        """ClaudeSDKClient raises prompt-too-long on attempt 1.

        On retry attempt 2, ``compact_transcript`` provides a smaller
        transcript and the stream succeeds.  The generator must NOT yield
        ``StreamError``.
        """
        import contextlib

        from backend.copilot.response_model import StreamError, StreamStart
        from backend.copilot.sdk.service import stream_chat_completion_sdk

        session = self._make_session()
        result_msg = self._make_result_message()
        attempt_count = [0]

        def _client_factory(*args, **kwargs):
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                return self._make_client_mock(raises_on_enter=True)
            return self._make_client_mock(result_message=result_msg)

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

        assert (
            attempt_count[0] == 2
        ), f"Expected 2 SDK attempts (retry), got {attempt_count[0]}"
        errors = [e for e in events if isinstance(e, StreamError)]
        assert not errors, f"Unexpected StreamError: {errors}"
        assert any(isinstance(e, StreamStart) for e in events)