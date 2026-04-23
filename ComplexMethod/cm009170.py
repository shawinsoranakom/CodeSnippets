def test_tools_and_structured_output() -> None:
    llm = ChatOpenAI(model="gpt-5-nano").with_structured_output(
        ResponseFormat, strict=True, include_raw=True, tools=[GenerateUsername]
    )

    expected_keys = {"raw", "parsing_error", "parsed"}
    query = "Hello"
    tool_query = "Generate a user name for Alice, black hair. Use the tool."
    # Test invoke
    ## Engage structured output
    response = llm.invoke(query)
    assert isinstance(response["parsed"], ResponseFormat)
    ## Engage tool calling
    response_tools = llm.invoke(tool_query)
    ai_msg = response_tools["raw"]
    assert isinstance(ai_msg, AIMessage)
    assert ai_msg.tool_calls
    assert response_tools["parsed"] is None

    # Test stream
    aggregated: dict = {}
    for chunk in llm.stream(tool_query):
        assert isinstance(chunk, dict)
        assert all(key in expected_keys for key in chunk)
        aggregated = {**aggregated, **chunk}
    assert all(key in aggregated for key in expected_keys)
    assert isinstance(aggregated["raw"], AIMessage)
    assert aggregated["raw"].tool_calls
    assert aggregated["parsed"] is None