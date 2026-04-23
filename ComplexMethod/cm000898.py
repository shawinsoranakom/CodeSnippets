async def test_tail_parentuuid_rewired_to_prefix(self, mock_chat_config):
        """After compaction, the first tail entry's parentUuid must point to
        the last entry in the compressed prefix — not its original parent."""
        transcript = _make_thinking_transcript()

        compacted_msgs = [
            {"role": "user", "content": "[conversation summary]"},
            {"role": "assistant", "content": "Summarized response"},
        ]
        mock_result = type(
            "CompressResult",
            (),
            {
                "was_compacted": True,
                "messages": compacted_msgs,
                "original_token_count": 800,
                "token_count": 200,
                "messages_summarized": 4,
                "messages_dropped": 0,
            },
        )()
        with patch(
            "backend.copilot.transcript._run_compression",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await compact_transcript(transcript, model="test-model")

        assert result is not None
        lines = [ln for ln in result.strip().split("\n") if ln.strip()]
        entries = [json.loads(ln) for ln in lines]

        # Find the boundary: the compressed prefix ends just before the
        # first tail entry (last assistant in original transcript).
        tail_start = None
        for i, entry in enumerate(entries):
            msg = entry.get("message", {})
            if isinstance(msg.get("content"), list):
                # Structured content = preserved tail entry
                tail_start = i
                break

        assert tail_start is not None, "Could not find preserved tail entry"
        assert tail_start > 0, "Tail should not be the first entry"

        # The tail entry's parentUuid must be the uuid of the preceding entry
        prefix_last_uuid = entries[tail_start - 1]["uuid"]
        tail_first_parent = entries[tail_start]["parentUuid"]
        assert tail_first_parent == prefix_last_uuid, (
            f"Tail parentUuid {tail_first_parent!r} != "
            f"last prefix uuid {prefix_last_uuid!r}"
        )