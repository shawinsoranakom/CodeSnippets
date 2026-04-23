def test_stream_basic(self) -> None:
        """Test streaming returns AIMessageChunks via mocked SDK."""
        model = _make_model()
        model.client = MagicMock()
        model.client.chat.send.return_value = _MockSyncStream(
            [dict(c) for c in _STREAM_CHUNKS]
        )

        chunks = list(model.stream("Hello"))
        assert len(chunks) > 0
        assert all(isinstance(c, AIMessageChunk) for c in chunks)
        # Concatenated content should be "Hello world"
        full_content = "".join(c.content for c in chunks if isinstance(c.content, str))
        assert "Hello" in full_content
        assert "world" in full_content