def test_completion_request(server: RemoteOpenAIServer, model_name: str):
    # test input: str
    response = requests.post(
        server.url_for("pooling"),
        json={"model": model_name, "input": input_text, "encoding_format": "float"},
    )
    response.raise_for_status()
    poolings = PoolingResponse.model_validate(response.json())

    assert poolings.id is not None
    assert len(poolings.data) == 1
    assert len(poolings.data[0].data) == len(input_tokens)
    assert poolings.usage.completion_tokens == 0
    assert poolings.usage.prompt_tokens == len(input_tokens)
    assert poolings.usage.total_tokens == len(input_tokens)

    # test input: list[int]
    response = requests.post(
        server.url_for("pooling"),
        json={"model": model_name, "input": input_tokens, "encoding_format": "float"},
    )
    response.raise_for_status()
    poolings = PoolingResponse.model_validate(response.json())

    assert poolings.id is not None
    assert len(poolings.data) == 1
    assert len(poolings.data[0].data) == len(input_tokens)
    assert poolings.usage.completion_tokens == 0
    assert poolings.usage.prompt_tokens == len(input_tokens)
    assert poolings.usage.total_tokens == len(input_tokens)