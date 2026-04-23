async def test_astream_usage_only_chunk_emitted(self) -> None:
        """Test that an async usage-only chunk emits usage_metadata."""
        model = _make_model()
        model.client = MagicMock()
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
        model.client.chat.send_async = AsyncMock(
            return_value=_MockAsyncStream(chunks_with_separate_usage)
        )
        chunks = [c async for c in model.astream("Hello")]

        usage_chunks = [c for c in chunks if c.usage_metadata]
        assert len(usage_chunks) >= 1
        usage = usage_chunks[-1].usage_metadata
        assert usage is not None
        assert usage["input_tokens"] == 10
        assert usage["output_tokens"] == 5
        assert usage["total_tokens"] == 15