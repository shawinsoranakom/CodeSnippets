def test_stream(self, model: BaseChatModel) -> None:
        """Test to verify that `model.stream(simple_message)` works.

        This should pass for all integrations. Passing this test does not indicate
        a "streaming" implementation, but rather that the model can be used in a
        streaming context.

        ??? question "Troubleshooting"

            First, debug
            `langchain_tests.integration_tests.chat_models.ChatModelIntegrationTests.test_invoke`.
            because `stream` has a default implementation that calls `invoke` and
            yields the result as a single chunk.

            If that test passes but not this one, you should make sure your `_stream`
            method does not raise any exceptions, and that it yields valid
            `langchain_core.outputs.chat_generation.ChatGenerationChunk`
            objects like so:

            ```python
            yield ChatGenerationChunk(message=AIMessageChunk(content="chunk text"))
            ```

            The final chunk must have `chunk_position='last'` to signal stream
            completion. This enables proper parsing of `tool_call_chunks` into
            `tool_calls` on the aggregated message:

            ```python
            for i, token in enumerate(tokens):
                is_last = i == len(tokens) - 1
                yield ChatGenerationChunk(
                    message=AIMessageChunk(
                        content=token,
                        chunk_position="last" if is_last else None,
                    )
                )
            ```
        """
        chunks: list[AIMessageChunk] = []
        full: AIMessageChunk | None = None
        for chunk in model.stream("Hello"):
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