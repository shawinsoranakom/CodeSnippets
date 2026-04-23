async def test_extracts_code_from_response_with_text_before(self):
        """Should correctly extract and validate code when text comes before it."""
        response_with_text = {
            "result": f"""I apologize for the rate limit issue. Let me help you create the component.

Here's the implementation:

```python
{VALID_COMPONENT_CODE}
```

This component will process your input."""
        }

        with (
            patch(
                "langflow.agentic.services.assistant_service.classify_intent",
                side_effect=_mock_intent_classification("generate_component"),
            ),
            patch(
                "langflow.agentic.services.assistant_service.execute_flow_file_streaming",
                side_effect=_mock_streaming_result(response_with_text),
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

        validating_events = [e for e in parsed_events if e.get("event") == "progress" and e.get("step") == "validating"]
        assert len(validating_events) == 1

        complete_events = [e for e in parsed_events if e.get("event") == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0]["data"]["validated"] is True