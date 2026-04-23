def test_basic_roundtrip(self):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "world"},
        ]
        result = _messages_to_transcript(messages)
        assert result.endswith("\n")
        lines = result.strip().split("\n")
        assert len(lines) == 2

        user_entry = json.loads(lines[0])
        assert user_entry["type"] == "user"
        assert user_entry["message"]["role"] == "user"
        assert user_entry["message"]["content"] == "hello"
        assert user_entry["parentUuid"] == ""

        asst_entry = json.loads(lines[1])
        assert asst_entry["type"] == "assistant"
        assert asst_entry["message"]["role"] == "assistant"
        assert asst_entry["message"]["content"] == [{"type": "text", "text": "world"}]
        assert asst_entry["parentUuid"] == user_entry["uuid"]