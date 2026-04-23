def test_assistant_with_tool_calls_produces_tool_use_blocks(self):
        import json as _json

        from backend.copilot.model import ChatMessage
        from backend.copilot.sdk.service import _session_messages_to_transcript

        messages = [
            ChatMessage(role="user", content="List files"),
            ChatMessage(
                role="assistant",
                content="",
                tool_calls=[
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "bash",
                            "arguments": _json.dumps({"cmd": "ls -la"}),
                        },
                    }
                ],
            ),
        ]
        result = _session_messages_to_transcript(messages)
        entries = self._parse_jsonl(result)

        assert len(entries) == 2
        assistant_entry = entries[1]
        assert assistant_entry["type"] == "assistant"
        blocks = assistant_entry["message"]["content"]
        tool_use_blocks = [b for b in blocks if b.get("type") == "tool_use"]
        assert len(tool_use_blocks) == 1
        tu = tool_use_blocks[0]
        assert tu["id"] == "call_abc123"
        assert tu["name"] == "bash"
        assert tu["input"] == {"cmd": "ls -la"}