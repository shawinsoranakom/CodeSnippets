def test_reasoning(output_version: Literal["v0", "responses/v1", "v1"]) -> None:
    llm = ChatOpenAI(
        model="o4-mini", use_responses_api=True, output_version=output_version
    )
    response = llm.invoke("Hello", reasoning={"effort": "low"})
    assert isinstance(response, AIMessage)

    # Test init params + streaming
    llm = ChatOpenAI(
        model="o4-mini", reasoning={"effort": "low"}, output_version=output_version
    )
    full: BaseMessageChunk | None = None
    for chunk in llm.stream("Hello"):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessage)

    for msg in [response, full]:
        if output_version == "v0":
            assert msg.additional_kwargs["reasoning"]
        else:
            block_types = [block["type"] for block in msg.content]
            assert block_types == ["reasoning", "text"]