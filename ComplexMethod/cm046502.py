def test_basic_mapping(self):
        items = _chat_tool_calls_to_responses_output(
            [
                {
                    "id": "call_abc",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"city":"Paris"}',
                    },
                }
            ]
        )
        assert len(items) == 1
        assert items[0]["type"] == "function_call"
        assert items[0]["call_id"] == "call_abc"
        assert items[0]["name"] == "get_weather"
        assert items[0]["arguments"] == '{"city":"Paris"}'
        assert items[0]["status"] == "completed"
        assert items[0]["id"].startswith("fc_")