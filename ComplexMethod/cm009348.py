def test_code_interpreter() -> None:
    llm = ChatGroq(model="groq/compound-mini")
    input_message = {
        "role": "user",
        "content": (
            "Calculate the square root of 101 and show me the Python code you used."
        ),
    }
    full: AIMessageChunk | None = None
    for chunk in llm.stream([input_message]):
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert full.additional_kwargs["reasoning_content"]
    assert full.additional_kwargs["executed_tools"]
    assert [block["type"] for block in full.content_blocks] == [
        "reasoning",
        "server_tool_call",
        "server_tool_result",
        "text",
    ]

    next_message = {
        "role": "user",
        "content": "Now do the same for 102.",
    }
    response = llm.invoke([input_message, full, next_message])
    assert [block["type"] for block in response.content_blocks] == [
        "reasoning",
        "server_tool_call",
        "server_tool_result",
        "text",
    ]