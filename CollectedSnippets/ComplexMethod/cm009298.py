def test_stream_response_metadata_fields(self) -> None:
        """Test response-level metadata in streaming response_metadata."""
        model = _make_model()
        model.client = MagicMock()
        stream_chunks: list[dict[str, Any]] = [
            {
                "choices": [
                    {"delta": {"role": "assistant", "content": "Hi"}, "index": 0}
                ],
                "model": "anthropic/claude-sonnet-4-5",
                "system_fingerprint": "fp_stream123",
                "object": "chat.completion.chunk",
                "created": 1700000000.0,
                "id": "gen-stream-meta",
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
                "system_fingerprint": "fp_stream123",
                "object": "chat.completion.chunk",
                "created": 1700000000.0,
                "id": "gen-stream-meta",
            },
        ]
        model.client.chat.send.return_value = _MockSyncStream(stream_chunks)

        chunks = list(model.stream("Hello"))
        assert len(chunks) >= 2

        # Find the chunk with finish_reason (final metadata chunk)
        final = [
            c for c in chunks if c.response_metadata.get("finish_reason") == "stop"
        ]
        assert len(final) == 1
        meta = final[0].response_metadata
        assert meta["model_name"] == "anthropic/claude-sonnet-4-5"
        assert meta["system_fingerprint"] == "fp_stream123"
        assert meta["native_finish_reason"] == "end_turn"
        assert meta["finish_reason"] == "stop"
        assert meta["id"] == "gen-stream-meta"
        assert meta["created"] == 1700000000
        assert meta["object"] == "chat.completion.chunk"