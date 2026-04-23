async def test_response_with_apology_and_cutoff_code(self):
        """Should handle response with apology text and cut-off/incomplete code."""
        response_with_apology = {
            "result": f"""I apologize for the rate limit issue. Let me create the component.

Here's the implementation:

```python
{CUTOFF_COMPONENT_CODE}"""
        }

        with (
            patch(
                "langflow.agentic.services.assistant_service.classify_intent",
                side_effect=_mock_intent_classification("generate_component"),
            ),
            patch(
                "langflow.agentic.services.assistant_service.execute_flow_file_streaming",
                side_effect=_mock_streaming_result(response_with_apology),
            ),
        ):
            events = [
                event
                async for event in execute_flow_with_validation_streaming(
                    flow_filename="test.json",
                    input_value="create a sentiment analyzer",
                    global_variables={},
                    max_retries=0,
                )
            ]

        parsed_events = [json.loads(e[6:-2]) for e in events]

        validating_events = [e for e in parsed_events if e.get("event") == "progress" and e.get("step") == "validating"]
        assert len(validating_events) == 1, "Code should be extracted and validation attempted"

        complete_events = [e for e in parsed_events if e.get("event") == "complete"]
        assert len(complete_events) == 1

        complete_data = complete_events[0]["data"]
        assert complete_data["validated"] is False, "Incomplete code should fail validation"
        assert complete_data.get("validation_error") is not None, "Should have validation error"
        assert "component_code" in complete_data, "Should include extracted code"
        assert "SentimentAnalyzer" in complete_data["component_code"]