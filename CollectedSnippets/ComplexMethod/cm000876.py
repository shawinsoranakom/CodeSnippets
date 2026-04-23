async def test_authentication_error_breaks_immediately(self):
        """AuthenticationError breaks the retry loop without compaction.

        Authentication failures are non-context errors.  The generator must
        yield a single ``StreamError`` with a user-friendly message and NOT
        attempt transcript compaction or DB fallback.
        """
        import contextlib

        from backend.copilot.response_model import StreamError, StreamStart
        from backend.copilot.sdk.service import stream_chat_completion_sdk

        session = self._make_session()
        original_transcript = _build_transcript(
            [("user", "prior question"), ("assistant", "prior answer")]
        )

        auth_err = Exception("authentication failed: invalid API key")
        attempt_count = [0]

        def _patched_factory(*a, **kw):
            attempt_count[0] += 1
            cm = self._make_client_mock(raises_on_enter=False)
            cm.__aenter__.return_value.query.side_effect = auth_err
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

        # Should NOT retry — only 1 attempt for auth errors
        assert (
            attempt_count[0] == 1
        ), f"Expected 1 attempt (no retry for auth error), got {attempt_count[0]}"
        errors = [e for e in events if isinstance(e, StreamError)]
        assert errors, "Expected StreamError"
        assert errors[0].code == "sdk_stream_error"
        # Verify user-friendly message (not raw SDK text)
        assert "Authentication" in errors[0].errorText
        assert any(isinstance(e, StreamStart) for e in events)