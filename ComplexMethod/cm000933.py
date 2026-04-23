def test_simple_user_assistant_messages(self):
        from backend.copilot.model import ChatMessage
        from backend.copilot.sdk.service import _session_messages_to_transcript

        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there"),
        ]
        result = _session_messages_to_transcript(messages)
        entries = self._parse_jsonl(result)

        assert len(entries) == 2
        assert entries[0]["type"] == "user"
        assert entries[0]["message"]["role"] == "user"
        assert entries[0]["message"]["content"] == "Hello"
        assert entries[1]["type"] == "assistant"
        assert entries[1]["message"]["role"] == "assistant"
        content_blocks = entries[1]["message"]["content"]
        assert any(
            b.get("type") == "text" and b.get("text") == "Hi there"
            for b in content_blocks
        )