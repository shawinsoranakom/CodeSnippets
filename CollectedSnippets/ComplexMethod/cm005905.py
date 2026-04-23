async def test_flow_execution_error_on_component_generation_retries_then_emits_complete_event(self):
        """Component generation failures retry up to max_retries, then emit a complete event.

        Before the retry fix: a single flow-execution failure emitted format_error_event
        and returned immediately, so the user saw "An internal error occurred" with no
        retry attempts — even though the spec defines automatic retry on failure.

        After the fix: for component generation intent, each attempt that raises is
        surfaced via validation_failed + retrying progress events, and only when all
        attempts are exhausted is a final complete event emitted with validated=false
        so the frontend renders the "Component generation failed" card (NOT a bare
        error event).
        """
        from fastapi import HTTPException

        async def mock_streaming_error(*_args, **_kwargs):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
            yield  # pragma: no cover — makes this an async generator

        with (
            patch(
                "langflow.agentic.services.assistant_service.classify_intent",
                side_effect=_mock_intent_classification("generate_component"),
            ),
            patch(
                "langflow.agentic.services.assistant_service.execute_flow_file_streaming",
                side_effect=mock_streaming_error,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            events = [
                event
                async for event in execute_flow_with_validation_streaming(
                    flow_filename="test.json",
                    input_value="create a component",
                    global_variables={},
                    max_retries=3,
                )
            ]

        parsed_events = [json.loads(e[6:-2]) for e in events]

        # No bare error events — component generation failures go through the
        # validation_failed / complete pipeline so the frontend can render the card.
        error_events = [e for e in parsed_events if e.get("event") == "error"]
        assert len(error_events) == 0, f"Expected 0 error events for component generation, got: {error_events}"

        # Final event must be a complete event with validated=false and the friendly
        # rate-limit message preserved in validation_error.
        complete_events = [e for e in parsed_events if e.get("event") == "complete"]
        assert len(complete_events) == 1, f"Expected exactly 1 complete event, got: {complete_events}"
        complete_data = complete_events[0]["data"]
        assert complete_data["validated"] is False
        assert "rate limit" in complete_data["validation_error"].lower()
        # 4 attempts total (max_retries=3 → total_attempts=4)
        assert complete_data["validation_attempts"] == 4