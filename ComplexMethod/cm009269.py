def test_web_search() -> None:
    llm = ChatXAI(model=MODEL_NAME, temperature=0).bind_tools([{"type": "web_search"}])

    # Test invoke
    response = llm.invoke("Look up the current time in Boston, MA.")
    assert response.content
    content_types = {block["type"] for block in response.content_blocks}
    assert content_types == {"server_tool_call", "server_tool_result", "text"}
    assert response.content_blocks[0]["name"] == "web_search"  # type: ignore[typeddict-item]

    # Test streaming
    full: AIMessageChunk | None = None
    for chunk in llm.stream("Look up the current time in Boston, MA."):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    content_types = {block["type"] for block in full.content_blocks}
    assert content_types == {"server_tool_call", "server_tool_result", "text"}
    assert full.content_blocks[0]["name"] == "web_search"