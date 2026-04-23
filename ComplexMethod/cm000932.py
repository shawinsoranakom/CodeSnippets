async def test_econnreset_triggers_retry_and_succeeds(self):
        """Raw Exception('ECONNRESET') matching is_transient_api_error → retry succeeds.

        Simulates the generic Exception handler path — separate from
        _HandledStreamError.  Verifies the same retry mechanics apply:
        _next_transient_backoff + _do_transient_backoff + continue.
        """
        from unittest.mock import AsyncMock, MagicMock, patch

        from backend.copilot.constants import is_transient_api_error
        from backend.copilot.response_model import (
            StreamError,
            StreamFinish,
            StreamStatus,
        )
        from backend.copilot.sdk.service import (
            _do_transient_backoff,
            _next_transient_backoff,
        )

        transient_retries = 0
        max_transient_retries = 3
        attempt = 0
        _last_reset_attempt = -1
        emitted: list = []
        call_count = 0

        async def fake_stream():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("ECONNRESET")
            yield StreamFinish()

        state = MagicMock()
        state.usage = MagicMock()
        state.transcript_builder = MagicMock()
        state.transcript_builder.snapshot.return_value = ([], None)

        for _iteration in range(10):
            if attempt >= 3:
                break
            if attempt != _last_reset_attempt:
                transient_retries = 0
                _last_reset_attempt = attempt

            events_yielded = 0
            try:
                async for evt in fake_stream():
                    if not isinstance(evt, (StreamError, StreamStatus)):
                        events_yielded += 1
                    emitted.append(evt)
                break
            except Exception as exc:
                is_transient = is_transient_api_error(str(exc))
                state.transcript_builder.restore(state.transcript_builder.snapshot())
                if events_yielded == 0 and is_transient:
                    backoff, transient_retries = _next_transient_backoff(
                        events_yielded, transient_retries, max_transient_retries
                    )
                    if backoff is not None:
                        with patch("asyncio.sleep", new=AsyncMock()):
                            async for evt in _do_transient_backoff(
                                backoff, state, "m", "s"
                            ):
                                emitted.append(evt)
                        continue
                break

        # StreamStatus emitted during retry (notification to client)
        statuses = [e for e in emitted if isinstance(e, StreamStatus)]
        assert len(statuses) == 1

        # No StreamError — retry succeeded
        errors = [e for e in emitted if isinstance(e, StreamError)]
        assert len(errors) == 0

        # Content from successful second attempt
        finish_events = [e for e in emitted if isinstance(e, StreamFinish)]
        assert len(finish_events) == 1

        # Two total calls: first fails (ECONNRESET), second succeeds
        assert call_count == 2