async def test_parsed_dict_schema_async(schema: Any) -> None:
    llm = ChatOpenAI(model=MODEL_NAME, use_responses_api=True)
    response = await llm.ainvoke("how are ya", response_format=schema)
    parsed = json.loads(response.text)
    assert parsed == response.additional_kwargs["parsed"]
    assert parsed["response"]
    assert isinstance(parsed["response"], str)

    # Test stream
    full: BaseMessageChunk | None = None
    async for chunk in llm.astream("how are ya", response_format=schema):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    parsed = json.loads(full.text)
    assert parsed == full.additional_kwargs["parsed"]
    assert parsed["response"]
    assert isinstance(parsed["response"], str)