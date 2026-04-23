async def test_runnable_agent() -> None:
    """Simple test to verify that an agent built via composition works."""
    # Will alternate between responding with hello and goodbye
    infinite_cycle = cycle([AIMessage(content="hello world!")])
    # When streaming GenericFakeChatModel breaks AIMessage into chunks based on spaces
    model = GenericFakeChatModel(messages=infinite_cycle)

    template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are Cat Agent 007"),
            ("human", "{question}"),
        ],
    )

    def fake_parse(_: dict) -> AgentFinish | AgentAction:
        """A parser."""
        return AgentFinish(return_values={"foo": "meow"}, log="hard-coded-message")

    agent = template | model | fake_parse
    executor = AgentExecutor(agent=agent, tools=[])

    # Invoke
    result: Any = await asyncio.to_thread(executor.invoke, {"question": "hello"})
    assert result == {"foo": "meow", "question": "hello"}

    # ainvoke
    result = await executor.ainvoke({"question": "hello"})
    assert result == {"foo": "meow", "question": "hello"}

    # Batch
    result = await asyncio.to_thread(
        executor.batch,
        [{"question": "hello"}, {"question": "hello"}],
    )
    assert result == [
        {"foo": "meow", "question": "hello"},
        {"foo": "meow", "question": "hello"},
    ]

    # abatch
    result = await executor.abatch([{"question": "hello"}, {"question": "hello"}])
    assert result == [
        {"foo": "meow", "question": "hello"},
        {"foo": "meow", "question": "hello"},
    ]

    # Stream
    results = await asyncio.to_thread(list, executor.stream({"question": "hello"}))
    assert results == [
        {"foo": "meow", "messages": [AIMessage(content="hard-coded-message")]},
    ]

    # astream
    results = [r async for r in executor.astream({"question": "hello"})]
    assert results == [
        {
            "foo": "meow",
            "messages": [
                AIMessage(content="hard-coded-message"),
            ],
        },
    ]

    # stream log
    log_results: list[RunLogPatch] = [
        r async for r in executor.astream_log({"question": "hello"})
    ]
    # # Let's stream just the llm tokens.
    messages = []
    for log_record in log_results:
        for op in log_record.ops:
            if op["op"] == "add" and isinstance(op["value"], AIMessageChunk):
                messages.append(op["value"])  # noqa: PERF401

    assert messages != []

    # Aggregate state
    run_log = reduce(operator.add, log_results)

    assert isinstance(run_log, RunLog)

    assert run_log.state["final_output"] == {
        "foo": "meow",
        "messages": [AIMessage(content="hard-coded-message")],
    }