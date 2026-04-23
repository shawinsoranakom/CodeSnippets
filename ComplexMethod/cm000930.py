async def test_retry_succeeds_after_one_transient_handled_error(self):
        """_HandledStreamError(transient_api_error) → StreamStatus → success on retry.

        Simulates the retry loop logic directly, mirroring the real loop in
        stream_chat_completion_sdk.  Validates the composition of the three
        helper functions rather than calling stream_chat_completion_sdk (which
        requires DB/redis connections unavailable in unit tests).
        """
        from unittest.mock import AsyncMock, MagicMock, patch

        from backend.copilot.response_model import (
            StreamError,
            StreamFinish,
            StreamStatus,
        )
        from backend.copilot.sdk.service import (
            _do_transient_backoff,
            _HandledStreamError,
            _next_transient_backoff,
        )

        transient_retries = 0
        max_transient_retries = 3
        attempt = 0
        _last_reset_attempt = -1
        events_yielded = 0
        emitted: list = []

        call_count = 0

        async def fake_run_stream():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: raise transient error (not yet yielded to client)
                raise _HandledStreamError(
                    "transient", code="transient_api_error", already_yielded=False
                )
            # Second call: success — yield a content event
            yield StreamFinish()

        state = MagicMock()
        state.usage = MagicMock()
        state.transcript_builder = MagicMock()
        state.transcript_builder.snapshot.return_value = ([], None)

        # Replay the retry loop body for up to 10 iterations.
        for _iteration in range(10):
            if attempt >= 3:
                break
            if attempt != _last_reset_attempt:
                transient_retries = 0
                _last_reset_attempt = attempt

            events_yielded = 0

            try:
                async for evt in fake_run_stream():
                    if not isinstance(evt, (StreamError, StreamStatus)):
                        events_yielded += 1
                    emitted.append(evt)
                break  # success
            except _HandledStreamError as exc:
                state.transcript_builder.restore(state.transcript_builder.snapshot())
                if exc.code == "transient_api_error":
                    backoff, transient_retries = _next_transient_backoff(
                        events_yielded, transient_retries, max_transient_retries
                    )
                    if backoff is not None:
                        with patch("asyncio.sleep", new=AsyncMock()):
                            async for evt in _do_transient_backoff(
                                backoff, state, "msg-id", "sess-id"
                            ):
                                emitted.append(evt)
                        continue  # retry

        # StreamStatus emitted (retry notification)
        statuses = [e for e in emitted if isinstance(e, StreamStatus)]
        assert len(statuses) == 1
        assert (
            "retry" in statuses[0].message.lower()
            or "connection" in statuses[0].message.lower()
        )

        # No StreamError — transient error not surfaced when retry succeeded
        errors = [e for e in emitted if isinstance(e, StreamError)]
        assert len(errors) == 0

        # Content from successful second attempt is present
        content_events = [e for e in emitted if isinstance(e, StreamFinish)]
        assert len(content_events) == 1

        # Second attempt was called
        assert call_count == 2