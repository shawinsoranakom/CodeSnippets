async def test_handled_stream_error_transient_retries_then_succeeds(self):
        """_HandledStreamError(code="transient_api_error") triggers backoff retry.

        When ``_run_stream_attempt`` raises ``_HandledStreamError`` with
        ``code="transient_api_error"`` (i.e. an AssistantMessage with a transient
        error field arrives mid-stream), the outer loop must:
          1. Call ``_next_transient_backoff`` to get the sleep duration.
          2. Yield a ``StreamStatus`` message ("Connection interrupted…").
          3. Sleep for the backoff duration.
          4. Continue the loop and retry the same context-level attempt.
          5. NOT yield ``StreamError`` while retries remain.

        This exercises the ``_HandledStreamError`` handler path at
        ``stream_chat_completion_sdk`` line ~2335.
        """
        import contextlib

        from claude_agent_sdk import AssistantMessage, ResultMessage

        from backend.copilot.response_model import (
            StreamError,
            StreamStart,
            StreamStatus,
        )
        from backend.copilot.sdk.service import stream_chat_completion_sdk

        session = self._make_session()
        result_msg = self._make_result_message()
        call_count = [0]

        def _client_factory(*args, **kwargs):
            call_count[0] += 1
            attempt = call_count[0]

            async def _receive():
                if attempt == 1:
                    # First call: emit AssistantMessage with a transient error field
                    # so _run_stream_attempt detects is_transient_api_error and
                    # raises _HandledStreamError(code="transient_api_error").
                    yield AssistantMessage(
                        content=[],
                        model="claude-sonnet-4-20250514",
                        error="rate_limit",
                    )
                    yield ResultMessage(
                        subtype="error",
                        result="rate limit exceeded (status code 429)",
                        duration_ms=50,
                        duration_api_ms=0,
                        is_error=True,
                        num_turns=0,
                        session_id="test-session-id",
                    )
                else:
                    yield result_msg

            client = MagicMock()
            client.receive_response = _receive
            client.query = AsyncMock()
            client._transport = MagicMock()
            client._transport.write = AsyncMock()

            cm = AsyncMock()
            cm.__aenter__.return_value = client
            cm.__aexit__.return_value = None
            return cm

        original_transcript = _build_transcript(
            [("user", "prior question"), ("assistant", "prior answer")]
        )

        patches = _make_sdk_patches(
            session,
            original_transcript=original_transcript,
            compacted_transcript=None,
            client_side_effect=_client_factory,
        )

        events = []
        with contextlib.ExitStack() as stack:
            # Patch asyncio.sleep to avoid actual delays in the test.
            stack.enter_context(patch(f"{_SVC}.asyncio.sleep", new_callable=AsyncMock))
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

        # Two SDK client calls: first fails with transient error, second succeeds.
        assert (
            call_count[0] == 2
        ), f"Expected 2 SDK calls (transient retry), got {call_count[0]}"
        # No StreamError emitted — the retry succeeded.
        errors = [e for e in events if isinstance(e, StreamError)]
        assert (
            not errors
        ), f"Unexpected StreamError emitted during transient retry: {errors}"
        # StreamStatus("Connection interrupted…") must have been yielded.
        status_events = [e for e in events if isinstance(e, StreamStatus)]
        assert status_events, "Expected StreamStatus retry notification but got none"
        assert any(
            "retrying" in (e.message or "").lower()
            or "interrupted" in (e.message or "").lower()
            for e in status_events
        ), f"Expected 'retrying' or 'interrupted' in StreamStatus, got: {[e.message for e in status_events]}"
        assert any(isinstance(e, StreamStart) for e in events)