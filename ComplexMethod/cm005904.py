async def test_no_code_in_response_returns_as_is(self):
        """When response has no code (question intent), should return without validation."""
        text_only_response = {"result": "Langflow is a visual flow builder for LLM applications."}

        with (
            patch(
                "langflow.agentic.services.assistant_service.classify_intent",
                side_effect=_mock_intent_classification("question"),
            ),
            patch(
                "langflow.agentic.services.assistant_service.execute_flow_file_streaming",
                side_effect=_mock_streaming_result(text_only_response),
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

        generating_events = [e for e in parsed_events if e.get("event") == "progress" and e.get("step") == "generating"]
        assert len(generating_events) == 1

        validating_events = [e for e in parsed_events if e.get("event") == "progress" and e.get("step") == "validating"]
        assert len(validating_events) == 0

        complete_events = [e for e in parsed_events if e.get("event") == "complete"]
        assert len(complete_events) == 1
        assert "validated" not in complete_events[0]["data"]