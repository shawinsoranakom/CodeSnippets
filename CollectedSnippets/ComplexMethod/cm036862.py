def test_commentary_with_function_recipient_creates_function_call(self):
        """Test commentary with recipient='functions.X' creates function calls."""
        message = Message.from_role_and_content(
            Role.ASSISTANT, '{"location": "San Francisco", "units": "celsius"}'
        )
        message = message.with_channel("commentary")
        message = message.with_recipient("functions.get_weather")

        output_items = harmony_to_response_output(message)

        assert len(output_items) == 1
        assert isinstance(output_items[0], ResponseFunctionToolCall)
        assert output_items[0].type == "function_call"
        assert output_items[0].name == "get_weather"
        assert (
            output_items[0].arguments
            == '{"location": "San Francisco", "units": "celsius"}'
        )
        assert output_items[0].call_id.startswith("call_")
        assert output_items[0].id.startswith("fc_")