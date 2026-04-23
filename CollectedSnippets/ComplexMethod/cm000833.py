def test_strips_non_anthropic_thinking_with_placeholder_signature(self):
        """OpenRouter's Anthropic-compat shim can emit thinking blocks
        from non-Anthropic producers (Kimi K2.6, DeepSeek) with a
        PLACEHOLDER signature string that passes the "non-empty string"
        check but fails Anthropic's cryptographic validation on replay.

        Observed in session 864a55ba after model-toggle from standard
        (Kimi) to advanced (Opus): the CLI session upload included a
        thinking block with ``signature="ANTHROPIC_SHIM_PLACEHOLDER"``
        (or similar), Opus 4.7 rejected with 400 ``Invalid `signature`
        in `thinking` block``.  Fix: strip thinking blocks from the
        LAST assistant turn whenever the producing ``model`` isn't an
        ``anthropic/*`` slug, regardless of signature presence."""
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
                "id": "msg_kimi_shim",
                "model": "moonshotai/kimi-k2.6-20260420",
                "content": [
                    # Placeholder signature — non-empty but cryptographically
                    # invalid for Anthropic.  Legacy strip (signature-only)
                    # would KEEP this block.
                    {
                        "type": "thinking",
                        "thinking": "shimmed reasoning",
                        "signature": "PLACEHOLDER_SHIM_SIG_abc123",
                    },
                    {"type": "text", "text": "answer"},
                ],
            },
        }
        content = _make_jsonl(user, asst)
        result = strip_for_upload(content)
        entries = [json.loads(line) for line in result.strip().split("\n")]
        asst_entry = next(
            e for e in entries if e.get("message", {}).get("id") == "msg_kimi_shim"
        )
        types = [
            b["type"] for b in asst_entry["message"]["content"] if isinstance(b, dict)
        ]
        assert "thinking" not in types, (
            "Non-Anthropic thinking block must be stripped even when it "
            "carries a placeholder signature — replay-to-Opus otherwise "
            "400s with Invalid signature"
        )
        assert "text" in types