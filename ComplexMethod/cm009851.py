async def test_agent_with_callbacks() -> None:
    """Test react chain with callbacks by setting verbose globally."""
    handler1 = FakeCallbackHandler()
    handler2 = FakeCallbackHandler()

    tool = "Search"
    responses = [
        f"FooBarBaz\nAction: {tool}\nAction Input: misalignment",
        "Oh well\nFinal Answer: curses foiled again",
    ]
    # Only fake LLM gets callbacks for handler2
    fake_llm = FakeListLLM(responses=responses, callbacks=[handler2])
    tools = [
        Tool(
            name="Search",
            func=lambda x: x,
            description="Useful for searching",
        ),
    ]
    agent = initialize_agent(
        tools,
        fake_llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    )

    output = await agent.arun("when was langchain made", callbacks=[handler1])
    assert output == "curses foiled again"

    # 1 top level chain run runs, 2 LLMChain runs, 2 LLM runs, 1 tool run
    assert handler1.chain_starts == handler1.chain_ends == 3
    assert handler1.llm_starts == handler1.llm_ends == 2
    assert handler1.tool_starts == 1
    assert handler1.tool_ends == 1
    # 1 extra agent action
    assert handler1.starts == 7
    # 1 extra agent end
    assert handler1.ends == 7
    assert handler1.errors == 0
    # during LLMChain
    assert handler1.text == 2

    assert handler2.llm_starts == 2
    assert handler2.llm_ends == 2
    assert (
        handler2.chain_starts
        == handler2.tool_starts
        == handler2.tool_ends
        == handler2.chain_ends
        == 0
    )