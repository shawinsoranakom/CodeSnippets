async def test_tool_from_runnable() -> None:
    prompt = (
        SystemMessagePromptTemplate.from_template("You are a nice assistant.")
        + "{question}"
    )
    llm = FakeStreamingListLLM(responses=["foo-lish"])

    chain = prompt | llm | StrOutputParser()

    chain_tool = tool("chain_tool", chain)

    assert isinstance(chain_tool, BaseTool)
    assert chain_tool.name == "chain_tool"
    assert chain_tool.run({"question": "What up"}) == chain.invoke(
        {"question": "What up"}
    )
    assert await chain_tool.arun({"question": "What up"}) == await chain.ainvoke(
        {"question": "What up"}
    )
    assert chain_tool.description.endswith(repr(chain))
    assert _schema(chain_tool.args_schema) == chain.get_input_jsonschema()
    assert _schema(chain_tool.args_schema) == {
        "properties": {"question": {"title": "Question", "type": "string"}},
        "title": "PromptInput",
        "type": "object",
        "required": ["question"],
    }