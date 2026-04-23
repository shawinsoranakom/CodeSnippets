async def test_replay_chat_completion_client_create_stream() -> None:
    num_messages = 5
    messages = [f"Message {i}" for i in range(num_messages)]
    reply_model_client = ReplayChatCompletionClient(messages)

    for i in range(num_messages):
        chunks: List[str] = []
        result: CreateResult | None = None
        async for completion in reply_model_client.create_stream([UserMessage(content="dummy", source="_")]):
            if isinstance(completion, CreateResult):
                result = completion
            else:
                assert isinstance(completion, str)
                chunks.append(completion)
        assert result is not None
        assert "".join(chunks) == messages[i] == result.content

    with pytest.raises(ValueError, match="No more mock responses available"):
        await reply_model_client.create([UserMessage(content="dummy", source="_")])