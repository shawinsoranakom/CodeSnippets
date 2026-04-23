async def test_response_with_apology_and_cutoff_code_with_retries(self):
        """After exhausting retries with cutoff code, should return validated=False."""
        cutoff_response = {
            "result": f"""I apologize for the issue.

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
                side_effect=_mock_streaming_result(cutoff_response),
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
        assert len(generating_events) == 3

        validating_events = [e for e in parsed_events if e.get("event") == "progress" and e.get("step") == "validating"]
        assert len(validating_events) == 3

        complete_events = [e for e in parsed_events if e.get("event") == "complete"]
        complete_data = complete_events[0]["data"]

        assert complete_data["validated"] is False
        assert complete_data["validation_attempts"] == 3