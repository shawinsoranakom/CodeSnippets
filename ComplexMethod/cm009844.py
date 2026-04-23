async def test_runnable_agent_with_function_calls() -> None:
    """Test agent with intermediate agent actions."""
    # Will alternate between responding with hello and goodbye
    infinite_cycle = cycle(
        [
            AIMessage(content="looking for pet..."),
            AIMessage(content="Found Pet"),
        ],
    )
    model = GenericFakeChatModel(messages=infinite_cycle)

    template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are Cat Agent 007"),
            ("human", "{question}"),
        ],
    )

    parser_responses = cycle(
        [
            AgentAction(
                tool="find_pet",
                tool_input={
                    "pet": "cat",
                },
                log="find_pet()",
            ),
            AgentFinish(
                return_values={"foo": "meow"},
                log="hard-coded-message",
            ),
        ],
    )

    def fake_parse(_: dict) -> AgentFinish | AgentAction:
        """A parser."""
        return cast("AgentFinish | AgentAction", next(parser_responses))

    @tool
    def find_pet(pet: str) -> str:
        """Find the given pet."""
        if pet != "cat":
            msg = "Only cats allowed"
            raise ValueError(msg)
        return "Spying from under the bed."

    agent = template | model | fake_parse
    executor = AgentExecutor(agent=agent, tools=[find_pet])

    # Invoke
    result = await asyncio.to_thread(executor.invoke, {"question": "hello"})
    assert result == {"foo": "meow", "question": "hello"}

    # ainvoke
    result = await executor.ainvoke({"question": "hello"})
    assert result == {"foo": "meow", "question": "hello"}

    # astream
    results = [r async for r in executor.astream({"question": "hello"})]
    assert results == [
        {
            "actions": [
                AgentAction(
                    tool="find_pet",
                    tool_input={"pet": "cat"},
                    log="find_pet()",
                ),
            ],
            "messages": [AIMessage(content="find_pet()")],
        },
        {
            "messages": [HumanMessage(content="Spying from under the bed.")],
            "steps": [
                AgentStep(
                    action=AgentAction(
                        tool="find_pet",
                        tool_input={"pet": "cat"},
                        log="find_pet()",
                    ),
                    observation="Spying from under the bed.",
                ),
            ],
        },
        {"foo": "meow", "messages": [AIMessage(content="hard-coded-message")]},
    ]

    # astream log

    messages = []
    async for patch in executor.astream_log({"question": "hello"}):
        messages.extend(
            [
                op["value"].content
                for op in patch.ops
                if op["op"] == "add"
                and isinstance(op["value"], AIMessageChunk)
                and op["value"].content != ""
            ]
        )

    assert messages == ["looking", " ", "for", " ", "pet...", "Found", " ", "Pet"]