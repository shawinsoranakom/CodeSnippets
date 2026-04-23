async def test_openai_agent_tools_agent() -> None:
    """Test OpenAI tools agent."""
    infinite_cycle = cycle(
        [
            _make_tools_invocation(
                {
                    "find_pet": {"pet": "cat"},
                    "check_time": {},
                },
            ),
            AIMessage(content="The cat is spying from under the bed."),
        ],
    )

    GenericFakeChatModel.bind_tools = lambda self, _: self  # type: ignore[assignment,misc]
    model = GenericFakeChatModel(messages=infinite_cycle)

    @tool
    def find_pet(pet: str) -> str:
        """Find the given pet."""
        if pet != "cat":
            msg = "Only cats allowed"
            raise ValueError(msg)
        return "Spying from under the bed."

    @tool
    def check_time() -> str:
        """Find the given pet."""
        return "It's time to pet the cat."

    template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful AI bot. Your name is kitty power meow."),
            ("human", "{question}"),
            MessagesPlaceholder(
                variable_name="agent_scratchpad",
            ),
        ],
    )

    # type error due to base tool type below -- would need to be adjusted on tool
    # decorator.
    openai_agent = create_openai_tools_agent(
        model,
        [find_pet],
        template,
    )
    tool_calling_agent = create_tool_calling_agent(
        model,
        [find_pet],
        template,
    )
    for agent in [openai_agent, tool_calling_agent]:
        executor = AgentExecutor(agent=agent, tools=[find_pet])

        # Invoke
        result = await asyncio.to_thread(executor.invoke, {"question": "hello"})
        assert result == {
            "output": "The cat is spying from under the bed.",
            "question": "hello",
        }

        # astream
        chunks = [chunk async for chunk in executor.astream({"question": "hello"})]
        assert chunks == [
            {
                "actions": [
                    OpenAIToolAgentAction(
                        tool="find_pet",
                        tool_input={"pet": "cat"},
                        log="\nInvoking: `find_pet` with `{'pet': 'cat'}`\n\n\n",
                        message_log=[
                            _AnyIdAIMessageChunk(
                                content="",
                                additional_kwargs={
                                    "tool_calls": [
                                        {
                                            "function": {
                                                "name": "find_pet",
                                                "arguments": '{"pet": "cat"}',
                                            },
                                            "id": "0",
                                        },
                                        {
                                            "function": {
                                                "name": "check_time",
                                                "arguments": "{}",
                                            },
                                            "id": "1",
                                        },
                                    ],
                                },
                                chunk_position="last",
                            ),
                        ],
                        tool_call_id="0",
                    ),
                ],
                "messages": [
                    _AnyIdAIMessageChunk(
                        content="",
                        additional_kwargs={
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "find_pet",
                                        "arguments": '{"pet": "cat"}',
                                    },
                                    "id": "0",
                                },
                                {
                                    "function": {
                                        "name": "check_time",
                                        "arguments": "{}",
                                    },
                                    "id": "1",
                                },
                            ],
                        },
                        chunk_position="last",
                    ),
                ],
            },
            {
                "actions": [
                    OpenAIToolAgentAction(
                        tool="check_time",
                        tool_input={},
                        log="\nInvoking: `check_time` with `{}`\n\n\n",
                        message_log=[
                            _AnyIdAIMessageChunk(
                                content="",
                                additional_kwargs={
                                    "tool_calls": [
                                        {
                                            "function": {
                                                "name": "find_pet",
                                                "arguments": '{"pet": "cat"}',
                                            },
                                            "id": "0",
                                        },
                                        {
                                            "function": {
                                                "name": "check_time",
                                                "arguments": "{}",
                                            },
                                            "id": "1",
                                        },
                                    ],
                                },
                                chunk_position="last",
                            ),
                        ],
                        tool_call_id="1",
                    ),
                ],
                "messages": [
                    _AnyIdAIMessageChunk(
                        content="",
                        additional_kwargs={
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "find_pet",
                                        "arguments": '{"pet": "cat"}',
                                    },
                                    "id": "0",
                                },
                                {
                                    "function": {
                                        "name": "check_time",
                                        "arguments": "{}",
                                    },
                                    "id": "1",
                                },
                            ],
                        },
                        chunk_position="last",
                    ),
                ],
            },
            {
                "messages": [
                    FunctionMessage(
                        content="Spying from under the bed.",
                        name="find_pet",
                    ),
                ],
                "steps": [
                    AgentStep(
                        action=OpenAIToolAgentAction(
                            tool="find_pet",
                            tool_input={"pet": "cat"},
                            log="\nInvoking: `find_pet` with `{'pet': 'cat'}`\n\n\n",
                            message_log=[
                                _AnyIdAIMessageChunk(
                                    content="",
                                    additional_kwargs={
                                        "tool_calls": [
                                            {
                                                "function": {
                                                    "name": "find_pet",
                                                    "arguments": '{"pet": "cat"}',
                                                },
                                                "id": "0",
                                            },
                                            {
                                                "function": {
                                                    "name": "check_time",
                                                    "arguments": "{}",
                                                },
                                                "id": "1",
                                            },
                                        ],
                                    },
                                    chunk_position="last",
                                ),
                            ],
                            tool_call_id="0",
                        ),
                        observation="Spying from under the bed.",
                    ),
                ],
            },
            {
                "messages": [
                    FunctionMessage(
                        content="check_time is not a valid tool, "
                        "try one of [find_pet].",
                        name="check_time",
                    ),
                ],
                "steps": [
                    AgentStep(
                        action=OpenAIToolAgentAction(
                            tool="check_time",
                            tool_input={},
                            log="\nInvoking: `check_time` with `{}`\n\n\n",
                            message_log=[
                                _AnyIdAIMessageChunk(
                                    content="",
                                    additional_kwargs={
                                        "tool_calls": [
                                            {
                                                "function": {
                                                    "name": "find_pet",
                                                    "arguments": '{"pet": "cat"}',
                                                },
                                                "id": "0",
                                            },
                                            {
                                                "function": {
                                                    "name": "check_time",
                                                    "arguments": "{}",
                                                },
                                                "id": "1",
                                            },
                                        ],
                                    },
                                    chunk_position="last",
                                ),
                            ],
                            tool_call_id="1",
                        ),
                        observation="check_time is not a valid tool, "
                        "try one of [find_pet].",
                    ),
                ],
            },
            {
                "messages": [
                    AIMessage(content="The cat is spying from under the bed."),
                ],
                "output": "The cat is spying from under the bed.",
            },
        ]

        # astream_log
        log_patches = [
            log_patch async for log_patch in executor.astream_log({"question": "hello"})
        ]

        # Get the tokens from the astream log response.
        messages = []

        for log_patch in log_patches:
            for op in log_patch.ops:
                if op["op"] == "add" and isinstance(op["value"], AIMessageChunk):
                    value = op["value"]
                    if value.content:  # Filter out function call messages
                        messages.append(value.content)

        assert messages == [
            "The",
            " ",
            "cat",
            " ",
            "is",
            " ",
            "spying",
            " ",
            "from",
            " ",
            "under",
            " ",
            "the",
            " ",
            "bed.",
        ]