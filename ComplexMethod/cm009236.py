def test_builtin_tools_text_editor() -> None:
    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")  # type: ignore[call-arg]
    tool = {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"}
    llm_with_tools = llm.bind_tools([tool])
    response = llm_with_tools.invoke(
        "There's a syntax error in my primes.py file. Can you help me fix it?",
    )
    assert isinstance(response, AIMessage)
    assert response.tool_calls

    content_blocks = response.content_blocks
    assert len(content_blocks) == 2
    assert content_blocks[0]["type"] == "text"
    assert content_blocks[0]["text"]
    assert content_blocks[1]["type"] == "tool_call"
    assert content_blocks[1]["name"] == "str_replace_based_edit_tool"