async def test_prompt_async() -> None:
    prompt = ChatPromptTemplate.from_messages(
        messages=[
            SystemMessage(content="You are a nice assistant."),
            HumanMessagePromptTemplate.from_template("{question}"),
        ]
    )
    expected = ChatPromptValue(
        messages=[
            SystemMessage(content="You are a nice assistant."),
            HumanMessage(content="What is your name?"),
        ]
    )

    assert await prompt.ainvoke({"question": "What is your name?"}) == expected

    assert await prompt.abatch(
        [
            {"question": "What is your name?"},
            {"question": "What is your favorite color?"},
        ]
    ) == [
        expected,
        ChatPromptValue(
            messages=[
                SystemMessage(content="You are a nice assistant."),
                HumanMessage(content="What is your favorite color?"),
            ]
        ),
    ]

    assert [
        part async for part in prompt.astream({"question": "What is your name?"})
    ] == [expected]

    stream_log = [
        part async for part in prompt.astream_log({"question": "What is your name?"})
    ]

    assert len(stream_log[0].ops) == 1
    assert stream_log[0].ops[0]["op"] == "replace"
    assert stream_log[0].ops[0]["path"] == ""
    assert stream_log[0].ops[0]["value"]["logs"] == {}
    assert stream_log[0].ops[0]["value"]["final_output"] is None
    assert stream_log[0].ops[0]["value"]["streamed_output"] == []
    assert isinstance(stream_log[0].ops[0]["value"]["id"], str)

    assert stream_log[1:] == [
        RunLogPatch(
            {"op": "add", "path": "/streamed_output/-", "value": expected},
            {
                "op": "replace",
                "path": "/final_output",
                "value": ChatPromptValue(
                    messages=[
                        SystemMessage(content="You are a nice assistant."),
                        HumanMessage(content="What is your name?"),
                    ]
                ),
            },
        ),
    ]

    stream_log_state = [
        part
        async for part in prompt.astream_log(
            {"question": "What is your name?"}, diff=False
        )
    ]

    # remove random id
    stream_log[0].ops[0]["value"]["id"] = "00000000-0000-0000-0000-000000000000"
    stream_log_state[-1].ops[0]["value"]["id"] = "00000000-0000-0000-0000-000000000000"
    stream_log_state[-1].state["id"] = "00000000-0000-0000-0000-000000000000"

    # assert output with diff=False matches output with diff=True
    assert stream_log_state[-1].ops == [op for chunk in stream_log for op in chunk.ops]
    assert stream_log_state[-1] == RunLog(
        *[op for chunk in stream_log for op in chunk.ops],
        state={
            "final_output": ChatPromptValue(
                messages=[
                    SystemMessage(content="You are a nice assistant."),
                    HumanMessage(content="What is your name?"),
                ]
            ),
            "id": "00000000-0000-0000-0000-000000000000",
            "logs": {},
            "streamed_output": [
                ChatPromptValue(
                    messages=[
                        SystemMessage(content="You are a nice assistant."),
                        HumanMessage(content="What is your name?"),
                    ]
                )
            ],
            "type": "prompt",
            "name": "ChatPromptTemplate",
        },
    )

    # nested inside trace_with_chain_group

    async with atrace_as_chain_group("a_group") as manager:
        stream_log_nested = [
            part
            async for part in prompt.astream_log(
                {"question": "What is your name?"}, config={"callbacks": manager}
            )
        ]

    assert len(stream_log_nested[0].ops) == 1
    assert stream_log_nested[0].ops[0]["op"] == "replace"
    assert stream_log_nested[0].ops[0]["path"] == ""
    assert stream_log_nested[0].ops[0]["value"]["logs"] == {}
    assert stream_log_nested[0].ops[0]["value"]["final_output"] is None
    assert stream_log_nested[0].ops[0]["value"]["streamed_output"] == []
    assert isinstance(stream_log_nested[0].ops[0]["value"]["id"], str)

    assert stream_log_nested[1:] == [
        RunLogPatch(
            {"op": "add", "path": "/streamed_output/-", "value": expected},
            {
                "op": "replace",
                "path": "/final_output",
                "value": ChatPromptValue(
                    messages=[
                        SystemMessage(content="You are a nice assistant."),
                        HumanMessage(content="What is your name?"),
                    ]
                ),
            },
        ),
    ]