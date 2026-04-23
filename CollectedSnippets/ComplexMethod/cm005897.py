async def test_should_return_plain_text_for_qa_with_component_code(self):
        """Q&A response containing component code should NOT trigger validation.

        When intent is "question", code extraction is skipped entirely to prevent
        example code in explanatory answers from being treated as component generation.
        """
        component_code = (
            "from langflow.custom import Component\n\n"
            "class MyComponent(Component):\n"
            "    description = 'test'\n"
            "    inputs = []\n"
        )

        response_text = f"Here's an example:\n\n```python\n{component_code}\n```\n\nHope that helps!"
        flow_gen = _make_flow_events([("end", {"result": response_text})])

        with (
            patch(f"{MODULE}.classify_intent", new_callable=AsyncMock, return_value=_make_intent("question")),
            patch(f"{MODULE}.execute_flow_file_streaming", return_value=flow_gen()),
        ):
            gen = execute_flow_with_validation_streaming(
                flow_filename="TestFlow",
                input_value="how do I create a component?",
                global_variables={},
            )
            events = await _collect_events(gen)

            # Should NOT contain validation events — Q&A skips code extraction
            validation_events = [e for e in events if "extracting_code" in e or '"validating"' in e]
            assert len(validation_events) == 0

            # Should contain a complete event with the full text response
            complete_events = [e for e in events if '"event": "complete"' in e]
            assert len(complete_events) == 1