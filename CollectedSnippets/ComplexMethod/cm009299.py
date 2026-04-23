async def test_astream_response_metadata_fields(self) -> None:
        """Test response-level metadata in async streaming response_metadata."""
        model = _make_model()
        model.client = MagicMock()
        stream_chunks: list[dict[str, Any]] = [
            {
                "choices": [
                    {"delta": {"role": "assistant", "content": "Hi"}, "index": 0}
                ],
                "model": "anthropic/claude-sonnet-4-5",
                "system_fingerprint": "fp_async123",
                "object": "chat.completion.chunk",
                "created": 1700000000.0,
                "id": "gen-astream-meta",
            },
            {
                "choices": [
                    {
                        "delta": {},
                        "finish_reason": "stop",
                        "native_finish_reason": "end_turn",
                        "index": 0,
                    }
                ],
                "model": "anthropic/claude-sonnet-4-5",
                "system_fingerprint": "fp_async123",
                "object": "chat.completion.chunk",
                "created": 1700000000.0,
                "id": "gen-astream-meta",
            },
        ]
        model.client.chat.send_async = AsyncMock(
            return_value=_MockAsyncStream(stream_chunks)
        )

        chunks = [c async for c in model.astream("Hello")]
        assert len(chunks) >= 2

        # Find the chunk with finish_reason (final metadata chunk)
        final = [
            c for c in chunks if c.response_metadata.get("finish_reason") == "stop"
        ]
        assert len(final) == 1
        meta = final[0].response_metadata
        assert meta["model_name"] == "anthropic/claude-sonnet-4-5"
        assert meta["system_fingerprint"] == "fp_async123"
        assert meta["native_finish_reason"] == "end_turn"
        assert meta["id"] == "gen-astream-meta"
        assert meta["created"] == 1700000000
        assert meta["object"] == "chat.completion.chunk"