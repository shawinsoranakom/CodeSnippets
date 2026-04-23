def test_structured_output_and_tools(schema: Any) -> None:
    llm = ChatOpenAI(model="gpt-5-nano", verbosity="low").bind_tools(
        [GenerateUsername], strict=True, response_format=schema
    )

    response = llm.invoke("What weighs more, a pound of feathers or a pound of gold?")
    if schema == ResponseFormat:
        parsed = response.additional_kwargs["parsed"]
        assert isinstance(parsed, ResponseFormat)
    else:
        parsed = json.loads(response.text)
        assert isinstance(parsed, dict)
        assert parsed["response"]
        assert parsed["explanation"]

    # Test streaming tool calls
    full: BaseMessageChunk | None = None
    for chunk in llm.stream(
        "Generate a user name for Alice, black hair. Use the tool."
    ):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert len(full.tool_calls) == 1
    tool_call = full.tool_calls[0]
    assert tool_call["name"] == "GenerateUsername"