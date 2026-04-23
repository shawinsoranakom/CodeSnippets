def test_function_call_output_maps_to_tool_role(self):
        payload = ResponsesRequest(
            input = [
                {"role": "user", "content": "Weather?"},
                {
                    "type": "function_call",
                    "call_id": "call_1",
                    "name": "get_weather",
                    "arguments": "{}",
                },
                {
                    "type": "function_call_output",
                    "call_id": "call_1",
                    "output": '{"temp": 20}',
                },
            ],
        )
        msgs = _normalise_responses_input(payload)
        assert len(msgs) == 3
        assert msgs[0].role == "user"

        assert msgs[1].role == "assistant"
        assert msgs[1].tool_calls is not None
        assert msgs[1].tool_calls[0]["id"] == "call_1"
        assert msgs[1].tool_calls[0]["function"]["name"] == "get_weather"

        assert msgs[2].role == "tool"
        assert msgs[2].tool_call_id == "call_1"
        assert msgs[2].content == '{"temp": 20}'