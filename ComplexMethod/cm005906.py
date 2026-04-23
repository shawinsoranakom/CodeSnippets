async def test_flow_execution_error_on_qa_intent_emits_error_event_without_retry(self):
        """Q&A intent has no retry semantics — failures emit a bare error event immediately."""
        from fastapi import HTTPException

        call_count = 0

        async def mock_streaming_error(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
            yield  # pragma: no cover — makes this an async generator

        with (
            patch(
                "langflow.agentic.services.assistant_service.classify_intent",
                side_effect=_mock_intent_classification("question"),
            ),
            patch(
                "langflow.agentic.services.assistant_service.execute_flow_file_streaming",
                side_effect=mock_streaming_error,
            ),
        ):
            events = [
                event
                async for event in execute_flow_with_validation_streaming(
                    flow_filename="test.json",
                    input_value="what is langflow?",
                    global_variables={},
                    max_retries=3,
                )
            ]

        parsed_events = [json.loads(e[6:-2]) for e in events]

        # Q&A: exactly one call, no retry, bare error event
        assert call_count == 1, f"Expected 1 call for Q&A intent, got {call_count}"
        error_events = [e for e in parsed_events if e.get("event") == "error"]
        assert len(error_events) == 1
        assert "rate limit" in error_events[0]["message"].lower()