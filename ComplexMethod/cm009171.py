async def _test_stream(stream: AsyncIterator, expect_usage: bool) -> None:
        full: BaseMessageChunk | None = None
        chunks_with_token_counts = 0
        chunks_with_response_metadata = 0
        async for chunk in stream:
            assert isinstance(chunk.content, str)
            full = chunk if full is None else full + chunk
            assert isinstance(chunk, AIMessageChunk)
            if chunk.usage_metadata is not None:
                chunks_with_token_counts += 1
            if chunk.response_metadata and not set(
                chunk.response_metadata.keys()
            ).issubset({"model_provider", "output_version"}):
                chunks_with_response_metadata += 1
        assert isinstance(full, AIMessageChunk)
        if chunks_with_response_metadata != 1:
            msg = (
                "Expected exactly one chunk with metadata. "
                "AIMessageChunk aggregation can add these metadata. Check that "
                "this is behaving properly."
            )
            raise AssertionError(msg)
        assert full.response_metadata.get("finish_reason") is not None
        assert full.response_metadata.get("model_name") is not None
        if expect_usage:
            if chunks_with_token_counts != 1:
                msg = (
                    "Expected exactly one chunk with token counts. "
                    "AIMessageChunk aggregation adds counts. Check that "
                    "this is behaving properly."
                )
                raise AssertionError(msg)
            assert full.usage_metadata is not None
            assert full.usage_metadata["input_tokens"] > 0
            assert full.usage_metadata["output_tokens"] > 0
            assert full.usage_metadata["total_tokens"] > 0
        else:
            assert chunks_with_token_counts == 0
            assert full.usage_metadata is None