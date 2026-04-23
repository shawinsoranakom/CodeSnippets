def test_preserves_anthropic_thinking_with_valid_signature(self):
        """Sanity: an Anthropic-issued thinking block with a real
        signature on the last turn must NOT be stripped — Anthropic
        requires value-identity on replay."""
        user = {
            "type": "user",
            "uuid": "u1",
            "parentUuid": "",
            "message": {"role": "user", "content": "hi"},
        }
        asst = {
            "type": "assistant",
            "uuid": "a1",
            "parentUuid": "u1",
            "message": {
                "role": "assistant",
                "id": "msg_opus",
                "model": "anthropic/claude-4.7-opus-20260416",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "reasoning",
                        "signature": "REAL_ANTHROPIC_SIG_blob",
                    },
                    {"type": "text", "text": "answer"},
                ],
            },
        }
        content = _make_jsonl(user, asst)
        result = strip_for_upload(content)
        entries = [json.loads(line) for line in result.strip().split("\n")]
        asst_entry = next(
            e for e in entries if e.get("message", {}).get("id") == "msg_opus"
        )
        types = [
            b["type"] for b in asst_entry["message"]["content"] if isinstance(b, dict)
        ]
        assert (
            "thinking" in types
        ), "Anthropic-signed thinking on last turn must survive strip"
        assert "text" in types