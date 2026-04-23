async def test_non_context_error_breaks_immediately(self):
        """Non-context errors (network, auth) break the retry loop immediately.

        The generator must yield ``StreamError(code="sdk_stream_error")``
        without attempting compaction or DB fallback.
        """
        import contextlib

        from backend.copilot.response_model import StreamError, StreamStart
        from backend.copilot.sdk.service import stream_chat_completion_sdk

        session = self._make_session()
        original_transcript = _build_transcript(
            [("user", "prior question"), ("assistant", "prior answer")]
        )

        # A non-context error (network failure) — no prompt-too-long patterns
        network_err = Exception("Connection reset by peer")
        attempt_count = [0]

        def _client_factory(*a, **kw):
            attempt_count[0] += 1
            return self._make_client_mock(raises_on_enter=True)

        # Override the error to be a non-context error
        def _patched_factory(*a, **kw):
            attempt_count[0] += 1
            cm = self._make_client_mock(raises_on_enter=False)
            cm.__aenter__.return_value.query.side_effect = network_err
            return cm

        patches = _make_sdk_patches(
            session,
            original_transcript=original_transcript,
            compacted_transcript="compacted",
            client_side_effect=_patched_factory,
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

        # Should NOT retry — only 1 attempt for non-context errors
        assert attempt_count[0] == 1, (
            f"Expected 1 attempt (no retry for non-context error), "
            f"got {attempt_count[0]}"
        )
        errors = [e for e in events if isinstance(e, StreamError)]
        assert errors, "Expected StreamError"
        assert errors[0].code == "sdk_stream_error"
        assert any(isinstance(e, StreamStart) for e in events)