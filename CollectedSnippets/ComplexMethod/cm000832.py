def test_strips_signatureless_thinking_from_last_turn(self):
        """Kimi K2.6 (and other non-Anthropic OpenRouter providers) emit
        thinking blocks without the Anthropic ``signature`` field.  When
        a subsequent advanced-tier toggle replays the transcript to Opus,
        Anthropic's API rejects the signature-less block with ``Invalid
        `signature` in `thinking` block`` — so strip_for_upload must drop
        them from the LAST assistant entry too, not just stale ones."""
        user = {
            "type": "user",
            "uuid": "u1",
            "parentUuid": "",
            "message": {"role": "user", "content": "hi"},
        }
        # Last (and only) assistant entry with a Kimi-shape thinking block
        asst = {
            "type": "assistant",
            "uuid": "a1",
            "parentUuid": "u1",
            "message": {
                "role": "assistant",
                "id": "msg_kimi",
                "content": [
                    # No ``signature`` field → non-Anthropic provider
                    {"type": "thinking", "thinking": "kimi reasoning"},
                    {"type": "text", "text": "answer"},
                ],
            },
        }
        content = _make_jsonl(user, asst)
        result = strip_for_upload(content)
        entries = [json.loads(line) for line in result.strip().split("\n")]
        asst_entry = next(
            e for e in entries if e.get("message", {}).get("id") == "msg_kimi"
        )
        types = [
            b["type"] for b in asst_entry["message"]["content"] if isinstance(b, dict)
        ]
        assert "thinking" not in types, (
            "Signature-less thinking block on last turn must be stripped "
            "to prevent Anthropic API rejection on model-switch replay"
        )
        assert "text" in types, "Text content must survive stripping"