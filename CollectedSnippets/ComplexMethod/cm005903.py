async def test_all_retries_fail_returns_validation_error(self):
        """When all retries fail, should return validated=False with error."""
        invalid_response = {"result": f"```python\n{INVALID_COMPONENT_CODE}\n```"}

        with (
            patch(
                "langflow.agentic.services.assistant_service.classify_intent",
                side_effect=_mock_intent_classification("generate_component"),
            ),
            patch(
                "langflow.agentic.services.assistant_service.execute_flow_file_streaming",
                side_effect=_mock_streaming_result(invalid_response),
            ),
        ):
            events = [
                event
                async for event in execute_flow_with_validation_streaming(
                    flow_filename="test.json",
                    input_value="create a component",
                    global_variables={},
                    max_retries=2,
                )
            ]

        parsed_events = [json.loads(e[6:-2]) for e in events]

        generating_events = [
            e for e in parsed_events if e.get("event") == "progress" and e.get("step") == "generating_component"
        ]
        assert len(generating_events) == 3  # max_retries=2 means 3 total attempts

        complete_events = [e for e in parsed_events if e.get("event") == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0]["data"]["validated"] is False
        assert complete_events[0]["data"]["validation_error"] is not None
        assert complete_events[0]["data"]["validation_attempts"] == 3