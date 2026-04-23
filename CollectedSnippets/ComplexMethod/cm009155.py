async def test_json_mode_async(llm: AzureChatOpenAI) -> None:
    response = await llm.ainvoke(
        "Return this as json: {'a': 1}", response_format={"type": "json_object"}
    )
    assert isinstance(response.content, str)
    assert json.loads(response.content) == {"a": 1}

    # Test streaming
    full: BaseMessageChunk | None = None
    async for chunk in llm.astream(
        "Return this as json: {'a': 1}", response_format={"type": "json_object"}
    ):
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert isinstance(full.content, str)
    assert json.loads(full.content) == {"a": 1}