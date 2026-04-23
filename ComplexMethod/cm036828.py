def test_tool_call_index_consistency_with_ongoing_call(self, mock_make_id):
        """
        Test that an ongoing tool call continuation and subsequent new calls
        maintain correct indexing when interleaved with content.
        """
        mock_make_id.side_effect = ["id_b", "id_c"]

        messages = [
            MockMessage(channel="commentary", recipient="functions.previous_tool")
        ]
        parser = MockStreamableParser(messages=messages)

        token_states = [
            TokenState("commentary", "functions.tool_a", '{"key_a": "val_a"}'),
            TokenState("final", None, "Thinking..."),
            TokenState("commentary", "functions.tool_b", '{"key_b": "val_b"}'),
            TokenState("final", None, " Thinking again..."),
            TokenState("commentary", "functions.tool_c", '{"key_c": "val_c"}'),
        ]

        delta_message, _ = extract_harmony_streaming_delta(
            harmony_parser=parser,
            token_states=token_states,
            prev_recipient="functions.tool_a",
            include_reasoning=False,
        )

        assert delta_message is not None

        tool_a_deltas = [t for t in delta_message.tool_calls if t.index == 1]
        assert len(tool_a_deltas) > 0
        assert tool_a_deltas[0].id is None
        assert tool_a_deltas[0].function.arguments == '{"key_a": "val_a"}'

        tool_b_header = next(t for t in delta_message.tool_calls if t.id == "id_b")
        assert tool_b_header.index == 2
        tool_b_args = next(
            t for t in delta_message.tool_calls if t.index == 2 and t.id is None
        )
        assert tool_b_args.function.arguments == '{"key_b": "val_b"}'

        tool_c_start = next(t for t in delta_message.tool_calls if t.id == "id_c")
        assert tool_c_start.index == 3
        tool_c_args = next(
            t for t in delta_message.tool_calls if t.index == 3 and t.id is None
        )
        assert tool_c_args.function.arguments == '{"key_c": "val_c"}'

        assert delta_message.content == "Thinking... Thinking again..."