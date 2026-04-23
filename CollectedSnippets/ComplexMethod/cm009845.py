async def test_runnable_with_multi_action_per_step() -> None:
    """Test an agent that can make multiple function calls at once."""
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
            [
                AgentAction(
                    tool="find_pet",
                    tool_input={
                        "pet": "cat",
                    },
                    log="find_pet()",
                ),
                AgentAction(
                    tool="pet_pet",  # A function that allows you to pet the given pet.
                    tool_input={
                        "pet": "cat",
                    },
                    log="pet_pet()",
                ),
            ],
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

    @tool
    def pet_pet(pet: str) -> str:
        """Pet the given pet."""
        if pet != "cat":
            msg = "Only cats should be petted."
            raise ValueError(msg)
        return "purrrr"

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
            "actions": [
                AgentAction(tool="pet_pet", tool_input={"pet": "cat"}, log="pet_pet()"),
            ],
            "messages": [AIMessage(content="pet_pet()")],
        },
        {
            # By-default observation gets converted into human message.
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
        {
            "messages": [
                HumanMessage(
                    content="pet_pet is not a valid tool, try one of [find_pet].",
                ),
            ],
            "steps": [
                AgentStep(
                    action=AgentAction(
                        tool="pet_pet",
                        tool_input={"pet": "cat"},
                        log="pet_pet()",
                    ),
                    observation="pet_pet is not a valid tool, try one of [find_pet].",
                ),
            ],
        },
        {"foo": "meow", "messages": [AIMessage(content="hard-coded-message")]},
    ]

    # astream log

    messages = []
    async for patch in executor.astream_log({"question": "hello"}):
        for op in patch.ops:
            if op["op"] != "add":
                continue

            value = op["value"]

            if not isinstance(value, AIMessageChunk):
                continue

            if value.content == "":  # Then it's a function invocation message
                continue

            messages.append(value.content)

    assert messages == ["looking", " ", "for", " ", "pet...", "Found", " ", "Pet"]