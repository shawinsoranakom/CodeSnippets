async def test_last_assistant_thinking_blocks_preserved(self, mock_chat_config):
        """After compaction, the last assistant entry must retain its
        original thinking and redacted_thinking blocks verbatim."""
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
        assert validate_transcript(result)

        last_content = _last_assistant_content(result)
        assert last_content is not None, "No assistant entry found"
        assert isinstance(last_content, list)

        # The last assistant must have the thinking blocks preserved
        block_types = [b["type"] for b in last_content]
        assert (
            "thinking" in block_types
        ), "thinking block missing from last assistant message"
        assert (
            "redacted_thinking" in block_types
        ), "redacted_thinking block missing from last assistant message"
        assert "text" in block_types

        # Verify the thinking block content is value-identical
        thinking_blocks = [b for b in last_content if b["type"] == "thinking"]
        assert len(thinking_blocks) == 1
        assert thinking_blocks[0]["thinking"] == THINKING_BLOCK["thinking"]
        assert thinking_blocks[0]["signature"] == THINKING_BLOCK["signature"]

        redacted_blocks = [b for b in last_content if b["type"] == "redacted_thinking"]
        assert len(redacted_blocks) == 1
        assert redacted_blocks[0]["data"] == REDACTED_THINKING_BLOCK["data"]