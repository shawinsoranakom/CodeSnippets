def test_function_calling_and_structured_output(schema: Any) -> None:
    def multiply(x: int, y: int) -> int:
        """return x * y"""
        return x * y

    llm = ChatOpenAI(model=MODEL_NAME, use_responses_api=True)
    bound_llm = llm.bind_tools([multiply], response_format=schema, strict=True)
    # Test structured output
    response = llm.invoke("how are ya", response_format=schema)
    if schema == Foo:
        parsed = schema(**json.loads(response.text))
        assert parsed.response
    else:
        parsed = json.loads(response.text)
        assert parsed["response"]
    assert parsed == response.additional_kwargs["parsed"]

    # Test function calling
    ai_msg = cast(AIMessage, bound_llm.invoke("whats 5 * 4"))
    assert len(ai_msg.tool_calls) == 1
    assert ai_msg.tool_calls[0]["name"] == "multiply"
    assert set(ai_msg.tool_calls[0]["args"]) == {"x", "y"}