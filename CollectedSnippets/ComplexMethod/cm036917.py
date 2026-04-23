def test_thinking_plus_tool_use_in_assistant_message(self):
        """thinking + tool_use: reasoning field set, tool_calls populated."""
        request = _make_request(
            [
                {"role": "user", "content": "What is 2+2?"},
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "thinking",
                            "thinking": "I need to call the calculator.",
                            "signature": "sig_tool",
                        },
                        {
                            "type": "tool_use",
                            "id": "call_001",
                            "name": "calculator",
                            "input": {"expression": "2+2"},
                        },
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "call_001",
                            "content": "4",
                        }
                    ],
                },
            ]
        )
        result = _convert(request)

        asst_msgs = [m for m in result.messages if m.get("role") == "assistant"]
        assert len(asst_msgs) == 1
        asst = asst_msgs[0]

        assert asst.get("reasoning") == "I need to call the calculator."
        tool_calls = list(asst.get("tool_calls", []))
        assert len(tool_calls) == 1
        assert tool_calls[0]["function"]["name"] == "calculator"
        # No text content alongside reasoning + tool_use.
        assert asst.get("content") is None