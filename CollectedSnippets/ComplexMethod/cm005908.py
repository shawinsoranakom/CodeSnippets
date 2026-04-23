async def test_complete_event_includes_component_code(self):
        """Complete event should include the extracted component_code field."""
        mock_flow_result = {"result": f"```python\n{VALID_COMPONENT_CODE}\n```"}

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
                    input_value="create a component",
                    global_variables={},
                    max_retries=3,
                )
            ]

        parsed_events = [json.loads(e[6:-2]) for e in events]

        complete_events = [e for e in parsed_events if e.get("event") == "complete"]
        assert len(complete_events) == 1

        complete_data = complete_events[0]["data"]
        assert "component_code" in complete_data
        assert "HelloWorldComponent" in complete_data["component_code"]