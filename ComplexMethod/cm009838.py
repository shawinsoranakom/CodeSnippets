async def test_agent_async_iterator_with_callbacks() -> None:
    """Test react chain async iterator with callbacks by setting verbose globally."""
    handler1 = FakeCallbackHandler()
    handler2 = FakeCallbackHandler()

    bad_action_name = "BadAction"
    responses = [
        f"I'm turning evil\nAction: {bad_action_name}\nAction Input: misalignment",
        "Oh well\nFinal Answer: curses foiled again",
    ]
    fake_llm = FakeListLLM(cache=False, responses=responses, callbacks=[handler2])

    tools = [
        Tool(
            name="Search",
            func=lambda x: x,
            description="Useful for searching",
        ),
        Tool(
            name="Lookup",
            func=lambda x: x,
            description="Useful for looking up things in a table",
        ),
    ]

    agent = initialize_agent(
        tools,
        fake_llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )
    agent_async_iter = agent.iter(
        inputs="when was langchain made",
        callbacks=[handler1],
        include_run_info=True,
    )
    assert isinstance(agent_async_iter, AgentExecutorIterator)

    outputs = list(agent_async_iter)

    assert outputs[-1]["output"] == "curses foiled again"
    assert isinstance(outputs[-1][RUN_KEY].run_id, UUID)

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