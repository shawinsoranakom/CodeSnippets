async def test_parsed_pydantic_schema_async() -> None:
    llm = ChatOpenAI(model=MODEL_NAME, use_responses_api=True)
    response = await llm.ainvoke("how are ya", response_format=Foo)
    parsed = Foo(**json.loads(response.text))
    assert parsed == response.additional_kwargs["parsed"]
    assert parsed.response

    # Test stream
    full: BaseMessageChunk | None = None
    async for chunk in llm.astream("how are ya", response_format=Foo):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    parsed = Foo(**json.loads(full.text))
    assert parsed == full.additional_kwargs["parsed"]
    assert parsed.response