def test_usage_only_chunk_emitted(self) -> None:
        """Test that a usage-only chunk (no choices) emits usage_metadata."""
        model = _make_model()
        model.client = MagicMock()
        # Content chunks followed by a usage-only chunk (no choices key)
        chunks_with_separate_usage: list[dict[str, Any]] = [
            {
                "choices": [
                    {"delta": {"role": "assistant", "content": "Hi"}, "index": 0}
                ],
                "model": MODEL_NAME,
                "object": "chat.completion.chunk",
                "created": 1700000000.0,
                "id": "gen-1",
            },
            {
                "choices": [{"delta": {}, "finish_reason": "stop", "index": 0}],
                "model": MODEL_NAME,
                "object": "chat.completion.chunk",
                "created": 1700000000.0,
                "id": "gen-1",
            },
            # Usage-only final chunk — no choices
            {
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
                "model": MODEL_NAME,
                "object": "chat.completion.chunk",
                "created": 1700000000.0,
                "id": "gen-1",
            },
        ]
        model.client.chat.send.return_value = _MockSyncStream(
            chunks_with_separate_usage
        )
        chunks = list(model.stream("Hello"))

        # Last chunk should carry usage_metadata
        usage_chunks = [c for c in chunks if c.usage_metadata]
        assert len(usage_chunks) >= 1
        usage = usage_chunks[-1].usage_metadata
        assert usage is not None
        assert usage["input_tokens"] == 10
        assert usage["output_tokens"] == 5
        assert usage["total_tokens"] == 15