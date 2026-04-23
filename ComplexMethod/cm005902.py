async def test_invalid_code_retries_until_success(self):
        """When code is invalid, should retry with error context until valid."""
        invalid_response = {"result": f"```python\n{INVALID_COMPONENT_CODE}\n```"}
        valid_response = {"result": f"```python\n{VALID_COMPONENT_CODE}\n```"}

        with (
            patch(
                "langflow.agentic.services.assistant_service.classify_intent",
                side_effect=_mock_intent_classification("generate_component"),
            ),
            patch(
                "langflow.agentic.services.assistant_service.execute_flow_file_streaming",
                side_effect=_mock_streaming_sequence([invalid_response, valid_response]),
            ),
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

        generating_events = [
            e for e in parsed_events if e.get("event") == "progress" and e.get("step") == "generating_component"
        ]
        assert len(generating_events) == 2

        validating_events = [e for e in parsed_events if e.get("event") == "progress" and e.get("step") == "validating"]
        assert len(validating_events) == 2

        complete_events = [e for e in parsed_events if e.get("event") == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0]["data"]["validated"] is True
        assert complete_events[0]["data"]["validation_attempts"] == 2