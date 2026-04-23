def test_json_mode(llm: AzureChatOpenAI) -> None:
    response = llm.invoke(
        "Return this as json: {'a': 1}", response_format={"type": "json_object"}
    )
    assert isinstance(response.content, str)
    assert json.loads(response.content) == {"a": 1}

    # Test streaming
    full: BaseMessageChunk | None = None
    for chunk in llm.stream(
        "Return this as json: {'a': 1}", response_format={"type": "json_object"}
    ):
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert isinstance(full.content, str)
    assert json.loads(full.content) == {"a": 1}