async def test_r1_reasoning_content_streaming(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that reasoning_content in model_extra is correctly extracted and streamed."""

    async def _mock_create_stream(*args: Any, **kwargs: Any) -> AsyncGenerator[ChatCompletionChunk, None]:
        contentChunks = [None, None, "This is the main content"]
        reasoningChunks = ["This is the reasoning content 1", "This is the reasoning content 2", None]
        for i in range(len(contentChunks)):
            await asyncio.sleep(0.1)
            yield ChatCompletionChunk(
                id="id",
                choices=[
                    ChunkChoice(
                        finish_reason="stop" if i == len(contentChunks) - 1 else None,
                        index=0,
                        delta=ChoiceDelta(
                            content=contentChunks[i],
                            # The reasoning content is included in model_extra for hosted R1 models.
                            reasoning_content=reasoningChunks[i],  # type: ignore
                            role="assistant",
                        ),
                    ),
                ],
                created=0,
                model="r1",
                object="chat.completion.chunk",
                usage=CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            )

    async def _mock_create(*args: Any, **kwargs: Any) -> AsyncGenerator[ChatCompletionChunk, None]:
        return _mock_create_stream(*args, **kwargs)

    # Patch the client creation
    monkeypatch.setattr(AsyncCompletions, "create", _mock_create)
    # Create the client
    model_client = OpenAIChatCompletionClient(
        model="r1",
        api_key="",
        model_info={
            "family": ModelFamily.R1,
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "structured_output": False,
        },
    )
    # Test the create_stream method
    chunks: List[str | CreateResult] = []
    async for chunk in model_client.create_stream(messages=[UserMessage(content="Hello", source="user")]):
        chunks.append(chunk)

    # Verify that the chunks first stream the reasoning content and then the main content
    # Then verify that the final result has the correct content and thought
    assert len(chunks) == 5
    assert chunks[0] == "<think>This is the reasoning content 1"
    assert chunks[1] == "This is the reasoning content 2"
    assert chunks[2] == "</think>"
    assert chunks[3] == "This is the main content"
    assert isinstance(chunks[4], CreateResult)
    assert chunks[4].content == "This is the main content"
    assert chunks[4].thought == "This is the reasoning content 1This is the reasoning content 2"