def test_new_tool_call(self, mock_make_tool_call_id, channel):
        """Test new tool call creation when recipient changes."""
        mock_make_tool_call_id.return_value = "call_test123"
        parser = MockStreamableParser()

        token_states = [
            TokenState(channel=channel, recipient="functions.get_weather", text="")
        ]

        delta_message, tools_streamed = extract_harmony_streaming_delta(
            harmony_parser=parser,
            token_states=token_states,
            prev_recipient=None,
            include_reasoning=False,
        )

        assert delta_message is not None
        assert len(delta_message.tool_calls) == 1
        tool_call = delta_message.tool_calls[0]
        assert tool_call.id == "call_test123"
        assert tool_call.type == "function"
        assert tool_call.function.name == "get_weather"
        assert tool_call.function.arguments == ""
        assert tool_call.index == 0
        assert tools_streamed is True