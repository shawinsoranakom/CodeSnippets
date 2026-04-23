async def test_all_attempts_exhausted_yields_stream_error(self):
        """All 3 ClaudeSDKClient attempts fail with prompt-too-long.

        The generator must yield ``StreamError(code="all_attempts_exhausted")``
        with a user-friendly message, not raw SDK error text.
        """
        import contextlib

        from backend.copilot.response_model import StreamError, StreamStart
        from backend.copilot.sdk.service import stream_chat_completion_sdk

        session = self._make_session()
        original_transcript = _build_transcript(
            [("user", "prior question"), ("assistant", "prior answer")]
        )

        patches = _make_sdk_patches(
            session,
            original_transcript=original_transcript,
            compacted_transcript=None,  # compaction fails → DB fallback
            client_side_effect=lambda *a, **kw: self._make_client_mock(
                raises_on_enter=True
            ),
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

        errors = [e for e in events if isinstance(e, StreamError)]
        assert errors, "Expected StreamError but got none"
        err = errors[0]
        assert err.code == "all_attempts_exhausted"
        assert (
            "too long" in err.errorText.lower() or "new chat" in err.errorText.lower()
        )
        assert "context_length_exceeded" not in err.errorText
        assert any(isinstance(e, StreamStart) for e in events)