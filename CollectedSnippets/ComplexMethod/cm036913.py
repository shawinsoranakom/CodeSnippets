def test_completion_request_batched(server: RemoteOpenAIServer, model_name: str):
    N = 10
    input_texts = [input_text] * N

    response = requests.post(
        server.url_for("pooling"),
        json={"model": model_name, "input": input_texts, "encoding_format": "float"},
    )
    response.raise_for_status()
    poolings = PoolingResponse.model_validate(response.json())

    assert poolings.id is not None
    assert len(poolings.data) == N
    assert len(poolings.data[0].data) == len(input_tokens)
    assert poolings.usage.completion_tokens == 0
    assert poolings.usage.prompt_tokens == len(input_tokens) * N
    assert poolings.usage.total_tokens == len(input_tokens) * N

    # test list[list[int]]
    response = requests.post(
        server.url_for("pooling"),
        json={
            "model": model_name,
            "input": [input_tokens] * N,
            "encoding_format": "float",
        },
    )
    response.raise_for_status()
    poolings = PoolingResponse.model_validate(response.json())

    assert poolings.id is not None
    assert len(poolings.data) == N
    assert len(poolings.data[0].data) == len(input_tokens)
    assert poolings.usage.completion_tokens == 0
    assert poolings.usage.prompt_tokens == len(input_tokens) * N
    assert poolings.usage.total_tokens == len(input_tokens) * N