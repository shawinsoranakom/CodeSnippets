async def test_structured_output_with_streaming_tool_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    class AgentResponse(BaseModel):
        thoughts: str
        response: Literal["happy", "sad", "neutral"]

    raw_content = json.dumps(
        {
            "thoughts": "The user explicitly states that they are happy without any indication of sadness or neutrality.",
            "response": "happy",
        }
    )
    chunked_content = [raw_content[i : i + 5] for i in range(0, len(raw_content), 5)]
    assert "".join(chunked_content) == raw_content

    model = "gpt-4.1-nano-2025-04-14"

    # generate the list of mock chunk content
    mock_chunk_events = [
        MockChunkEvent(
            type="chunk",
            chunk=ChatCompletionChunk(
                id="id",
                choices=[
                    ChunkChoice(
                        finish_reason=None,
                        index=0,
                        delta=ChoiceDelta(
                            content=mock_chunk_content,
                            role="assistant",
                        ),
                    )
                ],
                created=0,
                model=model,
                object="chat.completion.chunk",
                usage=None,
            ),
        )
        for mock_chunk_content in chunked_content
    ]

    # add the tool call chunk.
    mock_chunk_events += [
        MockChunkEvent(
            type="chunk",
            chunk=ChatCompletionChunk(
                id="id",
                choices=[
                    ChunkChoice(
                        finish_reason="tool_calls",
                        index=0,
                        delta=ChoiceDelta(
                            content=None,
                            role="assistant",
                            tool_calls=[
                                ChoiceDeltaToolCall(
                                    id="1",
                                    index=0,
                                    type="function",
                                    function=ChoiceDeltaToolCallFunction(
                                        name="_pass_function",
                                        arguments=json.dumps({"input": "happy"}),
                                    ),
                                )
                            ],
                        ),
                    )
                ],
                created=0,
                model=model,
                object="chat.completion.chunk",
                usage=None,
            ),
        )
    ]

    async def _mock_create_stream(*args: Any) -> AsyncGenerator[MockChunkEvent, None]:
        async def _stream() -> AsyncGenerator[MockChunkEvent, None]:
            for mock_chunk_event in mock_chunk_events:
                await asyncio.sleep(0.1)
                yield mock_chunk_event

        return _stream()

    # Mock the context manager __aenter__ method which returns the stream.
    monkeypatch.setattr(AsyncChatCompletionStreamManager, "__aenter__", _mock_create_stream)

    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key="",
    )

    # Test that the openai client was called with the correct response format.
    chunks: List[str | CreateResult] = []
    async for chunk in model_client.create_stream(
        messages=[UserMessage(content="I am happy.", source="user")], json_output=AgentResponse
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert isinstance(chunks[-1], CreateResult)
    assert isinstance(chunks[-1].content, list)
    assert len(chunks[-1].content) == 1
    assert chunks[-1].content[0] == FunctionCall(
        id="1", name="_pass_function", arguments=json.dumps({"input": "happy"})
    )
    assert isinstance(chunks[-1].thought, str)
    response = AgentResponse.model_validate(json.loads(chunks[-1].thought))
    assert (
        response.thoughts
        == "The user explicitly states that they are happy without any indication of sadness or neutrality."
    )
    assert response.response == "happy"