def test_strips_progress_and_thinking(self):
        user = {
            "type": "user",
            "uuid": "u1",
            "parentUuid": "",
            "message": {"role": "user", "content": "hi"},
        }
        progress = {"type": "progress", "uuid": "p1", "parentUuid": "u1", "data": {}}
        asst_old = {
            "type": "assistant",
            "uuid": "a1",
            "parentUuid": "p1",
            "message": {
                "role": "assistant",
                "id": "msg_old",
                "content": [
                    {"type": "thinking", "thinking": "stale thinking"},
                    {"type": "text", "text": "old answer"},
                ],
            },
        }
        user2 = {
            "type": "user",
            "uuid": "u2",
            "parentUuid": "a1",
            "message": {"role": "user", "content": "next"},
        }
        asst_new = {
            "type": "assistant",
            "uuid": "a2",
            "parentUuid": "u2",
            "message": {
                "role": "assistant",
                "id": "msg_new",
                "content": [
                    # Anthropic-style thinking block — has a signature so
                    # ``_should_strip_thinking_block`` preserves it on the
                    # last turn.  Without the signature (e.g. emitted by
                    # Kimi K2.6 via OpenRouter) it would be stripped — see
                    # ``test_strips_signatureless_thinking_from_last_turn``.
                    {
                        "type": "thinking",
                        "thinking": "fresh thinking",
                        "signature": "anthropic-signed-blob",
                    },
                    {"type": "text", "text": "new answer"},
                ],
            },
        }
        content = _make_jsonl(user, progress, asst_old, user2, asst_new)
        result = strip_for_upload(content)

        lines = result.strip().split("\n")
        # Progress should be stripped -> 4 entries remain
        assert len(lines) == 4

        # First entry (user) should be reparented since its child (progress) was stripped
        entries = [json.loads(line) for line in lines]
        types = [e.get("type") for e in entries]
        assert "progress" not in types

        # Old assistant thinking stripped, new assistant thinking preserved
        old_asst = next(
            e for e in entries if e.get("message", {}).get("id") == "msg_old"
        )
        old_content = old_asst["message"]["content"]
        old_types = [b["type"] for b in old_content if isinstance(b, dict)]
        assert "thinking" not in old_types
        assert "text" in old_types

        new_asst = next(
            e for e in entries if e.get("message", {}).get("id") == "msg_new"
        )
        new_content = new_asst["message"]["content"]
        new_types = [b["type"] for b in new_content if isinstance(b, dict)]
        assert "thinking" in new_types