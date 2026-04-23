async def test_cutoff_code_retry_gets_valid_code(self):
        """If retry gets valid code, should return validated=True."""
        cutoff_response = {
            "result": f"""Error occurred.

```python
{CUTOFF_COMPONENT_CODE}"""
        }
        valid_response = {"result": f"```python\n{VALID_COMPONENT_CODE}\n```"}

        with (
            patch(
                "langflow.agentic.services.assistant_service.classify_intent",
                side_effect=_mock_intent_classification("generate_component"),
            ),
            patch(
                "langflow.agentic.services.assistant_service.execute_flow_file_streaming",
                side_effect=_mock_streaming_sequence([cutoff_response, cutoff_response, valid_response]),
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
        complete_data = complete_events[0]["data"]

        assert complete_data["validated"] is True
        assert complete_data["validation_attempts"] == 3
        assert complete_data["class_name"] == "HelloWorldComponent"