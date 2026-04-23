async def test_transient_handled_error_exhaustion_yields_stream_error(self):
        """When all transient retries exhausted, StreamError must be yielded."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from backend.copilot.constants import FRIENDLY_TRANSIENT_MSG
        from backend.copilot.response_model import StreamError, StreamStatus
        from backend.copilot.sdk.service import (
            _do_transient_backoff,
            _HandledStreamError,
            _next_transient_backoff,
        )

        transient_retries = 0
        max_transient_retries = 2  # exhaust after 2 retries
        attempt = 0
        _last_reset_attempt = -1
        emitted: list = []

        async def always_fail():
            raise _HandledStreamError(
                "transient",
                error_msg="API overloaded",
                code="transient_api_error",
                already_yielded=False,
            )
            # Satisfy the type checker — unreachable
            return
            yield  # noqa: B901

        state = MagicMock()
        state.usage = MagicMock()
        state.transcript_builder = MagicMock()
        state.transcript_builder.snapshot.return_value = ([], None)

        ended_with_stream_error = False

        for _iteration in range(20):
            if attempt >= 3:
                break
            if attempt != _last_reset_attempt:
                transient_retries = 0
                _last_reset_attempt = attempt

            events_yielded = 0
            try:
                async for evt in always_fail():
                    emitted.append(evt)
                break
            except _HandledStreamError as exc:
                state.transcript_builder.restore(state.transcript_builder.snapshot())
                if exc.code == "transient_api_error":
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
                # retries exhausted
                ended_with_stream_error = True
                if not exc.already_yielded:
                    emitted.append(
                        StreamError(
                            errorText=exc.error_msg or FRIENDLY_TRANSIENT_MSG,
                            code=exc.code or "transient_api_error",
                        )
                    )
                break

        # Two StreamStatus events emitted (one per retry before exhaustion)
        statuses = [e for e in emitted if isinstance(e, StreamStatus)]
        assert len(statuses) == max_transient_retries

        # One StreamError emitted after exhaustion
        errors = [e for e in emitted if isinstance(e, StreamError)]
        assert len(errors) == 1
        assert errors[0].code == "transient_api_error"

        assert ended_with_stream_error is True