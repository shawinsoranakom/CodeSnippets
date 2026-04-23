async def test_r1_think_field_not_present(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _mock_create_stream(*args: Any, **kwargs: Any) -> AsyncGenerator[ChatCompletionChunk, None]:
        chunks = ["Hello", " Another Hello", " Yet Another Hello"]
        for i, chunk in enumerate(chunks):
            await asyncio.sleep(0.1)
            yield ChatCompletionChunk(
                id="id",
                choices=[
                    ChunkChoice(
                        finish_reason="stop" if i == len(chunks) - 1 else None,
                        index=0,
                        delta=ChoiceDelta(
                            content=chunk,
                            role="assistant",
                        ),
                    ),
                ],
                created=0,
                model="r1",
                object="chat.completion.chunk",
                usage=CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            )

    async def _mock_create(*args: Any, **kwargs: Any) -> ChatCompletion | AsyncGenerator[ChatCompletionChunk, None]:
        stream = kwargs.get("stream", False)
        if not stream:
            await asyncio.sleep(0.1)
            return ChatCompletion(
                id="id",
                choices=[
                    Choice(
                        finish_reason="stop",
                        index=0,
                        message=ChatCompletionMessage(
                            content="Hello Another Hello Yet Another Hello", role="assistant"
                        ),
                    )
                ],
                created=0,
                model="r1",
                object="chat.completion",
                usage=CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            )
        else:
            return _mock_create_stream(*args, **kwargs)

    monkeypatch.setattr(AsyncCompletions, "create", _mock_create)

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

    # Warning completion when think field is not present.
    with pytest.warns(UserWarning, match="Could not find <think>..</think> field in model response content."):
        create_result = await model_client.create(messages=[UserMessage(content="I am happy.", source="user")])
        assert create_result.content == "Hello Another Hello Yet Another Hello"
        assert create_result.finish_reason == "stop"
        assert not create_result.cached
        assert create_result.thought is None

    # Stream completion with think field.
    with pytest.warns(UserWarning, match="Could not find <think>..</think> field in model response content."):
        chunks: List[str | CreateResult] = []
        async for chunk in model_client.create_stream(messages=[UserMessage(content="Hello", source="user")]):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert isinstance(chunks[-1], CreateResult)
        assert chunks[-1].content == "Hello Another Hello Yet Another Hello"
        assert chunks[-1].thought is None
        assert not chunks[-1].cached