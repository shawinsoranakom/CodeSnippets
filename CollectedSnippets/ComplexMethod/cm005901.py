async def test_valid_code_first_try_returns_validated(self):
        """When code is valid on first try, should return validated=True."""
        mock_flow_result = {"result": f"Here is your component:\n\n```python\n{VALID_COMPONENT_CODE}\n```"}

        with (
            patch(
                "langflow.agentic.services.assistant_service.classify_intent",
                side_effect=_mock_intent_classification("generate_component"),
            ),
            patch(
                "langflow.agentic.services.assistant_service.execute_flow_file_streaming",
                side_effect=_mock_streaming_result(mock_flow_result),
            ),
        ):
            events = [
                event
                async for event in execute_flow_with_validation_streaming(
                    flow_filename="test.json",
                    input_value="create a hello world component",
                    global_variables={},
                    max_retries=3,
                )
            ]

        assert len(events) >= 2

        parsed_events = []
        for event in events:
            json_str = event[6:-2]
            parsed_events.append(json.loads(json_str))

        generating_events = [
            e for e in parsed_events if e.get("event") == "progress" and e.get("step") == "generating_component"
        ]
        assert len(generating_events) == 1

        validating_events = [e for e in parsed_events if e.get("event") == "progress" and e.get("step") == "validating"]
        assert len(validating_events) == 1

        complete_events = [e for e in parsed_events if e.get("event") == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0]["data"]["validated"] is True
        assert complete_events[0]["data"]["class_name"] == "HelloWorldComponent"