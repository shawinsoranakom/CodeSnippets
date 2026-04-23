async def test_ollama() -> None:
    model = "deepseek-r1:1.5b"
    model_info: ModelInfo = {
        "function_calling": False,
        "json_output": False,
        "vision": False,
        "family": ModelFamily.R1,
        "structured_output": False,
    }
    # Check if the model is running locally.
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:11434/v1/models/{model}")
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        pytest.skip(f"{model} model is not running locally: {e}")
    except httpx.ConnectError as e:
        pytest.skip(f"Ollama is not running locally: {e}")

    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key="placeholder",
        base_url="http://localhost:11434/v1",
        model_info=model_info,
    )

    # Test basic completion with the Ollama deepseek-r1:1.5b model.
    create_result = await model_client.create(
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
    if model_info["family"] == ModelFamily.R1:
        assert create_result.thought is not None

    # Test streaming completion with the Ollama deepseek-r1:1.5b model.
    chunks: List[str | CreateResult] = []
    async for chunk in model_client.create_stream(
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
    if model_info["family"] == ModelFamily.R1:
        assert chunks[-1].thought is not None