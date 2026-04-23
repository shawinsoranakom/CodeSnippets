async def test_openai_agent_with_streaming() -> None:
    """Test openai agent with streaming."""
    infinite_cycle = cycle(
        [
            _make_func_invocation("find_pet", pet="cat"),
            AIMessage(content="The cat is spying from under the bed."),
        ],
    )

    model = GenericFakeChatModel(messages=infinite_cycle)

    @tool
    def find_pet(pet: str) -> str:
        """Find the given pet."""
        if pet != "cat":
            msg = "Only cats allowed"
            raise ValueError(msg)
        return "Spying from under the bed."

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
    agent = create_openai_functions_agent(
        model,
        [find_pet],
        template,
    )
    executor = AgentExecutor(agent=agent, tools=[find_pet])

    # Invoke
    result = await asyncio.to_thread(executor.invoke, {"question": "hello"})
    assert result == {
        "output": "The cat is spying from under the bed.",
        "question": "hello",
    }

    # astream
    chunks = [chunk async for chunk in executor.astream({"question": "hello"})]
    assert _recursive_dump(chunks) == [
        {
            "actions": [
                {
                    "log": "\nInvoking: `find_pet` with `{'pet': 'cat'}`\n\n\n",
                    "message_log": [
                        {
                            "additional_kwargs": {
                                "function_call": {
                                    "arguments": '{"pet": "cat"}',
                                    "name": "find_pet",
                                },
                            },
                            "content": "",
                            "name": None,
                            "response_metadata": {},
                            "type": "AIMessageChunk",
                        },
                    ],
                    "tool": "find_pet",
                    "tool_input": {"pet": "cat"},
                    "type": "AgentActionMessageLog",
                },
            ],
            "messages": [
                {
                    "additional_kwargs": {
                        "function_call": {
                            "arguments": '{"pet": "cat"}',
                            "name": "find_pet",
                        },
                    },
                    "chunk_position": "last",
                    "content": "",
                    "invalid_tool_calls": [],
                    "name": None,
                    "response_metadata": {},
                    "tool_call_chunks": [],
                    "tool_calls": [],
                    "type": "AIMessageChunk",
                    "usage_metadata": None,
                },
            ],
        },
        {
            "messages": [
                {
                    "additional_kwargs": {},
                    "content": "Spying from under the bed.",
                    "name": "find_pet",
                    "response_metadata": {},
                    "type": "function",
                },
            ],
            "steps": [
                {
                    "action": {
                        "log": "\nInvoking: `find_pet` with `{'pet': 'cat'}`\n\n\n",
                        "tool": "find_pet",
                        "tool_input": {"pet": "cat"},
                        "type": "AgentActionMessageLog",
                    },
                    "observation": "Spying from under the bed.",
                },
            ],
        },
        {
            "messages": [
                {
                    "additional_kwargs": {},
                    "content": "The cat is spying from under the bed.",
                    "invalid_tool_calls": [],
                    "name": None,
                    "response_metadata": {},
                    "tool_calls": [],
                    "type": "ai",
                    "usage_metadata": None,
                },
            ],
            "output": "The cat is spying from under the bed.",
        },
    ]

    #
    # # astream_log
    log_patches = [
        log_patch async for log_patch in executor.astream_log({"question": "hello"})
    ]

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