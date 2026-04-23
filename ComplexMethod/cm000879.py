async def test_assistant_message_error_content_prompt_too_long_triggers_compaction(
        self,
    ):
        """AssistantMessage.error="invalid_request" with content "Prompt is too long".

        The SDK returns error type "invalid_request" but puts the actual
        rejection message ("Prompt is too long") in the content blocks.
        The retry loop must detect this via content inspection (sdk_error
        being set confirms it's an error message, not user content).
        """
        import contextlib

        from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

        from backend.copilot.response_model import StreamError, StreamStart
        from backend.copilot.sdk.service import stream_chat_completion_sdk

        session = self._make_session()
        success_result = self._make_result_message()
        attempt_count = [0]

        def _client_factory(*args, **kwargs):
            attempt_count[0] += 1

            async def _receive_error():
                # SDK returns invalid_request with "Prompt is too long" in content.
                # ResultMessage.result is a non-PTL value ("done") to isolate
                # the AssistantMessage content detection path exclusively.
                yield AssistantMessage(
                    content=[TextBlock(text="Prompt is too long")],
                    model="<synthetic>",
                    error="invalid_request",
                )
                yield ResultMessage(
                    subtype="success",
                    result="done",
                    duration_ms=100,
                    duration_api_ms=0,
                    is_error=False,
                    num_turns=1,
                    session_id="test-session-id",
                )

            async def _receive_success():
                yield success_result

            client = MagicMock()
            client._transport = MagicMock()
            client._transport.write = AsyncMock()
            client.query = AsyncMock()
            if attempt_count[0] == 1:
                client.receive_response = _receive_error
            else:
                client.receive_response = _receive_success
            cm = AsyncMock()
            cm.__aenter__.return_value = client
            cm.__aexit__.return_value = None
            return cm

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
            f"Expected 2 SDK attempts (AssistantMessage error content 'Prompt is "
            f"too long' should trigger compaction retry), got {attempt_count[0]}"
        )
        errors = [e for e in events if isinstance(e, StreamError)]
        assert not errors, f"Unexpected StreamError: {errors}"
        assert any(isinstance(e, StreamStart) for e in events)