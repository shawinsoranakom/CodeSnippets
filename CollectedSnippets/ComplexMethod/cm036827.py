def test_complex_batch_permutation(self, mock_make_id):
        """
        Test a complex permutation: Reasoning -> Tool Call -> Content.
        This verifies that multiple distinct actions in one batch
        are all captured in the single DeltaMessage.
        """
        mock_make_id.return_value = "call_batch_test"
        parser = MockStreamableParser()

        token_states = [
            # 1. Reasoning
            TokenState("analysis", None, "Reasoning about query..."),
            # 2. Tool Calling
            TokenState("commentary", "functions.search", '{"query":'),
            TokenState("commentary", "functions.search", ' "vllm"}'),
            # 3. Final Content
            TokenState("final", None, "."),
        ]

        delta_message, tools_streamed = extract_harmony_streaming_delta(
            harmony_parser=parser,
            token_states=token_states,
            prev_recipient=None,
            include_reasoning=True,
        )

        assert delta_message is not None

        assert delta_message.reasoning == "Reasoning about query..."

        # We expect 2 objects for 1 logical tool call:
        # 1. The definition (id, name, type)
        # 2. The arguments payload
        assert len(delta_message.tool_calls) == 2

        header = delta_message.tool_calls[0]
        payload = delta_message.tool_calls[1]

        assert header.function.name == "search"
        assert header.id == "call_batch_test"
        assert header.index == 0

        assert payload.index == 0
        assert payload.function.arguments == '{"query": "vllm"}'

        assert delta_message.content == "."
        assert tools_streamed is True