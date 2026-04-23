def test_preserves_anthropic_thinking_on_non_last_turn(self):
        """Anthropic ``thinking`` blocks on NON-last turns carry real
        reasoning state that helps context continuity on ``--resume``.
        Keep them when the producing model is known-Anthropic with a
        valid signature; strip only when we can't validate safely
        (legacy callers with no model info — falls through to the
        old stale-strip rule).
        """
        user = {
            "type": "user",
            "uuid": "u1",
            "parentUuid": "",
            "message": {"role": "user", "content": "first"},
        }
        asst1 = {
            "type": "assistant",
            "uuid": "a1",
            "parentUuid": "u1",
            "message": {
                "role": "assistant",
                "id": "msg_opus_prev",
                "model": "anthropic/claude-4.7-opus-20260416",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "first-turn reasoning",
                        "signature": "ANTHROPIC_SIG_1",
                    },
                    {"type": "text", "text": "first answer"},
                ],
            },
        }
        user2 = {
            "type": "user",
            "uuid": "u2",
            "parentUuid": "a1",
            "message": {"role": "user", "content": "second"},
        }
        asst2 = {
            "type": "assistant",
            "uuid": "a2",
            "parentUuid": "u2",
            "message": {
                "role": "assistant",
                "id": "msg_opus_last",
                "model": "anthropic/claude-4.7-opus-20260416",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "last-turn reasoning",
                        "signature": "ANTHROPIC_SIG_2",
                    },
                    {"type": "text", "text": "last answer"},
                ],
            },
        }
        content = _make_jsonl(user, asst1, user2, asst2)
        result = strip_for_upload(content)
        entries = [json.loads(line) for line in result.strip().split("\n")]

        # Prior Opus turn's thinking must survive — valid Anthropic
        # block with signature.
        prev = next(
            e for e in entries if e.get("message", {}).get("id") == "msg_opus_prev"
        )
        prev_types = [b["type"] for b in prev["message"]["content"]]
        assert "thinking" in prev_types, (
            "Anthropic thinking block on a non-last turn must be "
            "preserved — it carries real reasoning state"
        )
        # Last turn's thinking also preserved.
        last = next(
            e for e in entries if e.get("message", {}).get("id") == "msg_opus_last"
        )
        last_types = [b["type"] for b in last["message"]["content"]]
        assert "thinking" in last_types