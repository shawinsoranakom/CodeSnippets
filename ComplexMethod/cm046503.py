def test_codex_full_shape_roundtrip(self):
        """End-to-end: developer + user + assistant(output_text) +
        function_call + function_call_output + reasoning in one request."""
        payload = ResponsesRequest(
            instructions = "Base instructions.",
            input = [
                {
                    "type": "message",
                    "role": "developer",
                    "content": [{"type": "input_text", "text": "Dev override."}],
                },
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Weather?"}],
                },
                {
                    "type": "reasoning",
                    "id": "rs_1",
                    "summary": [],
                },
                {
                    "type": "function_call",
                    "call_id": "call_1",
                    "name": "get_weather",
                    "arguments": "{}",
                },
                {
                    "type": "function_call_output",
                    "call_id": "call_1",
                    "output": '{"temp":20}',
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "It's 20°C.",
                            "annotations": [],
                            "logprobs": [],
                        }
                    ],
                },
                {"role": "user", "content": "And tomorrow?"},
            ],
        )
        msgs = _normalise_responses_input(payload)
        # Single leading merged system; no mid-conversation system.
        assert msgs[0].role == "system"
        assert sum(1 for m in msgs if m.role == "system") == 1
        assert "Base instructions." in msgs[0].content
        assert "Dev override." in msgs[0].content

        roles = [m.role for m in msgs[1:]]
        # Reasoning item is dropped. Order: user, assistant(tool_calls),
        # tool, assistant(text), user.
        assert roles == ["user", "assistant", "tool", "assistant", "user"]
        assert msgs[2].tool_calls is not None
        assert msgs[3].role == "tool"
        assert msgs[3].tool_call_id == "call_1"
        assert msgs[4].content == "It's 20°C."