def test_function_calling(output_version: Literal["v0", "responses/v1", "v1"]) -> None:
    def multiply(x: int, y: int) -> int:
        """return x * y"""
        return x * y

    llm = ChatOpenAI(model=MODEL_NAME, output_version=output_version)
    bound_llm = llm.bind_tools([multiply, {"type": "web_search_preview"}])
    ai_msg = cast(AIMessage, bound_llm.invoke("whats 5 * 4"))
    assert len(ai_msg.tool_calls) == 1
    assert ai_msg.tool_calls[0]["name"] == "multiply"
    assert set(ai_msg.tool_calls[0]["args"]) == {"x", "y"}

    full: Any = None
    for chunk in bound_llm.stream("whats 5 * 4"):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert len(full.tool_calls) == 1
    assert full.tool_calls[0]["name"] == "multiply"
    assert set(full.tool_calls[0]["args"]) == {"x", "y"}

    for msg in [ai_msg, full]:
        assert len(msg.content_blocks) == 1
        assert msg.content_blocks[0]["type"] == "tool_call"

    response = bound_llm.invoke("What was a positive news story from today?")
    _check_response(response)