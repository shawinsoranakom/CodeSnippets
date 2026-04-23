async def test_generic_exception_transient_retry_then_succeeds(self):
        """Raw Exception("ECONNRESET") from receive_response triggers backoff retry.

        When ``receive_response`` raises a raw ``Exception`` whose string
        matches a transient pattern (e.g. ECONNRESET), the generic ``except
        Exception`` handler at ``stream_chat_completion_sdk`` line ~2398 must:
          1. Detect ``is_transient_api_error(str(e))`` as True.
          2. Call ``_next_transient_backoff`` to get the sleep duration.
          3. Yield a ``StreamStatus`` message ("Connection interrupted…").
          4. Sleep for the backoff duration.
          5. Continue the loop and retry the same context-level attempt.
          6. NOT yield ``StreamError`` while retries remain.

        This exercises the generic ``Exception`` handler (ECONNRESET path) at
        ``stream_chat_completion_sdk`` line ~2398.
        """
        import contextlib

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

            if attempt == 1:
                # First call: receive_response raises ECONNRESET immediately
                return self._make_client_mock_mid_stream_error(
                    error=Exception("ECONNRESET: connection reset by peer"),
                    pre_error_messages=None,
                )
            return self._make_client_mock(result_message=result_msg)

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

        # Two SDK client calls: first fails with ECONNRESET, second succeeds.
        assert (
            call_count[0] == 2
        ), f"Expected 2 SDK calls (ECONNRESET transient retry), got {call_count[0]}"
        # No StreamError emitted — the retry succeeded.
        errors = [e for e in events if isinstance(e, StreamError)]
        assert (
            not errors
        ), f"Unexpected StreamError emitted during ECONNRESET retry: {errors}"
        # StreamStatus("Connection interrupted…") must have been yielded.
        status_events = [e for e in events if isinstance(e, StreamStatus)]
        assert status_events, "Expected StreamStatus retry notification but got none"
        assert any(
            "retrying" in (e.message or "").lower()
            or "interrupted" in (e.message or "").lower()
            for e in status_events
        ), f"Expected 'retrying' or 'interrupted' in StreamStatus, got: {[e.message for e in status_events]}"
        assert any(isinstance(e, StreamStart) for e in events)