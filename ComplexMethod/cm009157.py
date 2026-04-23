async def test_astream_response_format(llm: AzureChatOpenAI) -> None:
    full: BaseMessageChunk | None = None
    chunks = []
    async for chunk in llm.astream("how are ya", response_format=Foo):
        chunks.append(chunk)
        full = chunk if full is None else full + chunk
    assert len(chunks) > 1
    assert isinstance(full, AIMessageChunk)
    parsed = full.additional_kwargs["parsed"]
    assert isinstance(parsed, Foo)
    assert isinstance(full.content, str)
    parsed_content = json.loads(full.content)
    assert parsed.response == parsed_content["response"]