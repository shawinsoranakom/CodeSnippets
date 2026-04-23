def test_assistant_tool_use_maps_to_tool_calls(self):
        msgs = [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Let me search."},
                    {
                        "type": "tool_use",
                        "id": "tu_1",
                        "name": "web_search",
                        "input": {"query": "test"},
                    },
                ],
            }
        ]
        result = anthropic_messages_to_openai(msgs)
        assert len(result) == 1
        m = result[0]
        assert m["role"] == "assistant"
        assert m["content"] == "Let me search."
        assert len(m["tool_calls"]) == 1
        tc = m["tool_calls"][0]
        assert tc["id"] == "tu_1"
        assert tc["function"]["name"] == "web_search"
        assert json.loads(tc["function"]["arguments"]) == {"query": "test"}