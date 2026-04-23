async def test_astream(self, model: BaseChatModel) -> None:
        """Test to verify that `await model.astream(simple_message)` works.

        This should pass for all integrations. Passing this test does not indicate
        a "natively async" or "streaming" implementation, but rather that the model can
        be used in an async streaming context.

        ??? question "Troubleshooting"

            First, debug
            `langchain_tests.integration_tests.chat_models.ChatModelIntegrationTests.test_stream`.
            and
            `langchain_tests.integration_tests.chat_models.ChatModelIntegrationTests.test_ainvoke`.
            because `astream` has a default implementation that calls `_stream` in
            an async context if it is implemented, or `ainvoke` and yields the result
            as a single chunk if not.

            If those tests pass but not this one, you should make sure your `_astream`
            method does not raise any exceptions, and that it yields valid
            `langchain_core.outputs.chat_generation.ChatGenerationChunk`
            objects like so:

            ```python
            yield ChatGenerationChunk(message=AIMessageChunk(content="chunk text"))
            ```

            See `test_stream` troubleshooting for `chunk_position` requirements.
        """
        chunks: list[AIMessageChunk] = []
        full: AIMessageChunk | None = None
        async for chunk in model.astream("Hello"):
            assert chunk is not None
            assert isinstance(chunk, AIMessageChunk)
            assert isinstance(chunk.content, str | list)
            chunks.append(chunk)
            full = chunk if full is None else full + chunk
        assert len(chunks) > 0
        assert isinstance(full, AIMessageChunk)
        assert full.content
        assert len(full.content_blocks) == 1
        assert full.content_blocks[0]["type"] == "text"

        # Verify chunk_position signaling
        last_chunk = chunks[-1]
        assert last_chunk.chunk_position == "last", (
            f"Final chunk must have chunk_position='last', "
            f"got {last_chunk.chunk_position!r}"
        )