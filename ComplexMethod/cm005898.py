async def test_should_return_plain_text_when_question_response_contains_example_code(self):
        """Q&A response with example component code should NOT trigger validation.

        Bug: User asks "how do I create a custom component?" and the LLM responds
        with an explanation plus an example code snippet. The fallback code extraction
        detects 'class SumComponent(Component)' in the example and triggers the
        validation pipeline, showing a component card instead of the text answer.
        """
        # Use a raw string with triple-backtick code block (real markdown)
        explanation_with_example = (
            "To create a custom component, you need to:\n\n"
            "1. Create a Python file\n"
            "2. Define a class\n\n"
            "```python\n"
            "from lfx.custom import Component\n"
            "from lfx.io import Output\n"
            "from lfx.schema import Data\n\n"
            "class SumComponent(Component):\n"
            "    display_name = 'Sum'\n"
            "    description = 'Adds two numbers'\n"
            "    inputs = []\n"
            "    outputs = [Output(name='result', display_name='Result', method='run')]\n\n"
            "    def run(self) -> Data:\n"
            "        return Data(data={'result': 42})\n"
            "```\n"
        )
        flow_gen = _make_flow_events([("end", {"result": explanation_with_example})])

        with (
            patch(f"{MODULE}.classify_intent", new_callable=AsyncMock, return_value=_make_intent("question")),
            patch(f"{MODULE}.execute_flow_file_streaming", return_value=flow_gen()),
        ):
            gen = execute_flow_with_validation_streaming(
                flow_filename="TestFlow",
                input_value="how do I create a custom component?",
                global_variables={},
            )
            events = await _collect_events(gen)

            # Should NOT contain validation-related events (extracting_code, validating, validated)
            validation_events = [e for e in events if "extracting_code" in e or "validating" in e]
            assert len(validation_events) == 0, (
                f"Q&A response with example code should not trigger validation. "
                f"Got validation events: {validation_events}"
            )

            # Should contain a complete event with the full text (not component card)
            complete_events = [e for e in events if '"event": "complete"' in e]
            assert len(complete_events) == 1