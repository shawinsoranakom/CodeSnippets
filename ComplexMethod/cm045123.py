async def test_tool_calling_with_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _mock_create_stream(*args: Any, **kwargs: Any) -> AsyncGenerator[ChatCompletionChunk, None]:
        model = resolve_model(kwargs.get("model", "gpt-4o"))
        mock_chunks_content = ["Hello", " Another Hello", " Yet Another Hello"]
        mock_chunks = [
            # generate the list of mock chunk content
            MockChunkDefinition(
                chunk_choice=ChunkChoice(
                    finish_reason=None,
                    index=0,
                    delta=ChoiceDelta(
                        content=mock_chunk_content,
                        role="assistant",
                    ),
                ),
                usage=None,
            )
            for mock_chunk_content in mock_chunks_content
        ] + [
            # generate the function call chunk
            MockChunkDefinition(
                chunk_choice=ChunkChoice(
                    finish_reason="tool_calls",
                    index=0,
                    delta=ChoiceDelta(
                        content=None,
                        role="assistant",
                        tool_calls=[
                            ChoiceDeltaToolCall(
                                index=0,
                                id="1",
                                type="function",
                                function=ChoiceDeltaToolCallFunction(
                                    name="_pass_function",
                                    arguments=json.dumps({"input": "task"}),
                                ),
                            )
                        ],
                    ),
                ),
                usage=None,
            )
        ]
        for mock_chunk in mock_chunks:
            await asyncio.sleep(0.1)
            yield ChatCompletionChunk(
                id="id",
                choices=[mock_chunk.chunk_choice],
                created=0,
                model=model,
                object="chat.completion.chunk",
                usage=mock_chunk.usage,
            )

    async def _mock_create(*args: Any, **kwargs: Any) -> ChatCompletion | AsyncGenerator[ChatCompletionChunk, None]:
        stream = kwargs.get("stream", False)
        if not stream:
            raise ValueError("Stream is not False")
        else:
            return _mock_create_stream(*args, **kwargs)

    monkeypatch.setattr(AsyncCompletions, "create", _mock_create)

    model_client = OpenAIChatCompletionClient(model="gpt-4o", api_key="")
    pass_tool = FunctionTool(_pass_function, description="pass tool.")
    stream = model_client.create_stream(messages=[UserMessage(content="Hello", source="user")], tools=[pass_tool])
    chunks: List[str | CreateResult] = []
    async for chunk in stream:
        chunks.append(chunk)
    assert chunks[0] == "Hello"
    assert chunks[1] == " Another Hello"
    assert chunks[2] == " Yet Another Hello"
    assert isinstance(chunks[-1], CreateResult)
    assert chunks[-1].content == [FunctionCall(id="1", arguments=r'{"input": "task"}', name="_pass_function")]
    assert chunks[-1].finish_reason == "function_calls"
    assert chunks[-1].thought == "Hello Another Hello Yet Another Hello"