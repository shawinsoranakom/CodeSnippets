async def test_web_search_async() -> None:
    llm = ChatOpenAI(model=MODEL_NAME, output_version="v0")
    response = await llm.ainvoke(
        "What was a positive news story from today?",
        tools=[{"type": "web_search_preview"}],
    )
    _check_response(response)
    assert response.response_metadata["status"]

    # Test streaming
    full: BaseMessageChunk | None = None
    async for chunk in llm.astream(
        "What was a positive news story from today?",
        tools=[{"type": "web_search_preview"}],
    ):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    _check_response(full)

    for msg in [response, full]:
        assert msg.additional_kwargs["tool_outputs"]
        assert len(msg.additional_kwargs["tool_outputs"]) == 1
        tool_output = msg.additional_kwargs["tool_outputs"][0]
        assert tool_output["type"] == "web_search_call"