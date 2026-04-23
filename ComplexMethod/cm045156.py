async def test_ollama_create(model: str, ollama_client: OllamaChatCompletionClient) -> None:
    create_result = await ollama_client.create(
        messages=[
            UserMessage(
                content="Taking two balls from a bag of 10 green balls and 20 red balls, "
                "what is the probability of getting a green and a red balls?",
                source="user",
            ),
        ]
    )
    assert isinstance(create_result.content, str)
    assert len(create_result.content) > 0
    assert create_result.finish_reason == "stop"
    assert create_result.usage is not None

    chunks: List[str | CreateResult] = []
    async for chunk in ollama_client.create_stream(
        messages=[
            UserMessage(
                content="Taking two balls from a bag of 10 green balls and 20 red balls, "
                "what is the probability of getting a green and a red balls?",
                source="user",
            ),
        ]
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert isinstance(chunks[-1], CreateResult)
    assert chunks[-1].finish_reason == "stop"
    assert len(chunks[-1].content) > 0
    assert chunks[-1].usage is not None