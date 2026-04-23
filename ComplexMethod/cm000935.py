def test_tool_result_produces_tool_result_block(self):
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
                        "id": "call_xyz",
                        "type": "function",
                        "function": {
                            "name": "bash",
                            "arguments": _json.dumps({"cmd": "ls"}),
                        },
                    }
                ],
            ),
            ChatMessage(
                role="tool",
                tool_call_id="call_xyz",
                content="file1.txt\nfile2.txt\nfile3.txt",
            ),
        ]
        result = _session_messages_to_transcript(messages)
        entries = self._parse_jsonl(result)

        # user + assistant + user(tool_result)
        assert len(entries) == 3
        tool_result_entry = entries[2]
        assert tool_result_entry["type"] == "user"
        content = tool_result_entry["message"]["content"]
        assert isinstance(content, list)
        tr_blocks = [b for b in content if b.get("type") == "tool_result"]
        assert len(tr_blocks) == 1
        assert tr_blocks[0]["tool_use_id"] == "call_xyz"
        assert tr_blocks[0]["content"] == "file1.txt\nfile2.txt\nfile3.txt"