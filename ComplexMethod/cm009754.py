async def test_prompt_with_llm_parser(
    mocker: MockerFixture, snapshot: SnapshotAssertion
) -> None:
    prompt = (
        SystemMessagePromptTemplate.from_template("You are a nice assistant.")
        + "{question}"
    )
    llm = FakeStreamingListLLM(responses=["bear, dog, cat", "tomato, lettuce, onion"])
    parser = CommaSeparatedListOutputParser()

    chain = prompt | llm | parser

    assert isinstance(chain, RunnableSequence)
    assert chain.first == prompt
    assert chain.middle == [llm]
    assert chain.last == parser
    assert dumps(chain, pretty=True) == snapshot

    # Test invoke
    prompt_spy = mocker.spy(prompt.__class__, "ainvoke")
    llm_spy = mocker.spy(llm.__class__, "ainvoke")
    parser_spy = mocker.spy(parser.__class__, "ainvoke")
    tracer = FakeTracer()
    assert await chain.ainvoke(
        {"question": "What is your name?"}, {"callbacks": [tracer]}
    ) == ["bear", "dog", "cat"]
    assert prompt_spy.call_args.args[1] == {"question": "What is your name?"}
    assert llm_spy.call_args.args[1] == ChatPromptValue(
        messages=[
            SystemMessage(content="You are a nice assistant."),
            HumanMessage(content="What is your name?"),
        ]
    )
    assert parser_spy.call_args.args[1] == "bear, dog, cat"
    assert tracer.runs == snapshot
    mocker.stop(prompt_spy)
    mocker.stop(llm_spy)
    mocker.stop(parser_spy)

    # Test batch
    prompt_spy = mocker.spy(prompt.__class__, "abatch")
    llm_spy = mocker.spy(llm.__class__, "abatch")
    parser_spy = mocker.spy(parser.__class__, "abatch")
    tracer = FakeTracer()
    assert await chain.abatch(
        [
            {"question": "What is your name?"},
            {"question": "What is your favorite color?"},
        ],
        {"callbacks": [tracer]},
    ) == [["tomato", "lettuce", "onion"], ["bear", "dog", "cat"]]
    assert prompt_spy.call_args.args[1] == [
        {"question": "What is your name?"},
        {"question": "What is your favorite color?"},
    ]
    assert llm_spy.call_args.args[1] == [
        ChatPromptValue(
            messages=[
                SystemMessage(content="You are a nice assistant."),
                HumanMessage(content="What is your name?"),
            ]
        ),
        ChatPromptValue(
            messages=[
                SystemMessage(content="You are a nice assistant."),
                HumanMessage(content="What is your favorite color?"),
            ]
        ),
    ]
    assert parser_spy.call_args.args[1] == [
        "tomato, lettuce, onion",
        "bear, dog, cat",
    ]
    assert len(tracer.runs) == 2
    assert all(
        run.name == "RunnableSequence"
        and run.run_type == "chain"
        and len(run.child_runs) == 3
        for run in tracer.runs
    )
    mocker.stop(prompt_spy)
    mocker.stop(llm_spy)
    mocker.stop(parser_spy)

    # Test stream
    prompt_spy = mocker.spy(prompt.__class__, "ainvoke")
    llm_spy = mocker.spy(llm.__class__, "astream")
    tracer = FakeTracer()
    assert [
        token
        async for token in chain.astream(
            {"question": "What is your name?"}, {"callbacks": [tracer]}
        )
    ] == [["tomato"], ["lettuce"], ["onion"]]
    assert prompt_spy.call_args.args[1] == {"question": "What is your name?"}
    assert llm_spy.call_args.args[1] == ChatPromptValue(
        messages=[
            SystemMessage(content="You are a nice assistant."),
            HumanMessage(content="What is your name?"),
        ]
    )

    prompt_spy.reset_mock()
    llm_spy.reset_mock()
    stream_log = [
        part async for part in chain.astream_log({"question": "What is your name?"})
    ]

    # Remove IDs from logs
    for part in stream_log:
        for op in part.ops:
            if (
                isinstance(op["value"], dict)
                and "id" in op["value"]
                and not isinstance(op["value"]["id"], list)  # serialized lc id
            ):
                del op["value"]["id"]

    expected = [
        RunLogPatch(
            {
                "op": "replace",
                "path": "",
                "value": {
                    "logs": {},
                    "final_output": None,
                    "streamed_output": [],
                    "name": "RunnableSequence",
                    "type": "chain",
                },
            }
        ),
        RunLogPatch(
            {
                "op": "add",
                "path": "/logs/ChatPromptTemplate",
                "value": {
                    "end_time": None,
                    "final_output": None,
                    "metadata": {},
                    "name": "ChatPromptTemplate",
                    "start_time": "2023-01-01T00:00:00.000+00:00",
                    "streamed_output": [],
                    "streamed_output_str": [],
                    "tags": ["seq:step:1"],
                    "type": "prompt",
                },
            }
        ),
        RunLogPatch(
            {
                "op": "add",
                "path": "/logs/ChatPromptTemplate/final_output",
                "value": ChatPromptValue(
                    messages=[
                        SystemMessage(content="You are a nice assistant."),
                        HumanMessage(content="What is your name?"),
                    ]
                ),
            },
            {
                "op": "add",
                "path": "/logs/ChatPromptTemplate/end_time",
                "value": "2023-01-01T00:00:00.000+00:00",
            },
        ),
        RunLogPatch(
            {
                "op": "add",
                "path": "/logs/FakeStreamingListLLM",
                "value": {
                    "end_time": None,
                    "final_output": None,
                    "metadata": {
                        "ls_model_type": "llm",
                        "ls_provider": "fakestreaminglist",
                    },
                    "name": "FakeStreamingListLLM",
                    "start_time": "2023-01-01T00:00:00.000+00:00",
                    "streamed_output": [],
                    "streamed_output_str": [],
                    "tags": ["seq:step:2"],
                    "type": "llm",
                },
            }
        ),
        RunLogPatch(
            {
                "op": "add",
                "path": "/logs/FakeStreamingListLLM/final_output",
                "value": {
                    "generations": [
                        [
                            {
                                "generation_info": None,
                                "text": "bear, dog, cat",
                                "type": "Generation",
                            }
                        ]
                    ],
                    "llm_output": None,
                    "run": None,
                    "type": "LLMResult",
                },
            },
            {
                "op": "add",
                "path": "/logs/FakeStreamingListLLM/end_time",
                "value": "2023-01-01T00:00:00.000+00:00",
            },
        ),
        RunLogPatch(
            {
                "op": "add",
                "path": "/logs/CommaSeparatedListOutputParser",
                "value": {
                    "end_time": None,
                    "final_output": None,
                    "metadata": {},
                    "name": "CommaSeparatedListOutputParser",
                    "start_time": "2023-01-01T00:00:00.000+00:00",
                    "streamed_output": [],
                    "streamed_output_str": [],
                    "tags": ["seq:step:3"],
                    "type": "parser",
                },
            }
        ),
        RunLogPatch(
            {
                "op": "add",
                "path": "/logs/CommaSeparatedListOutputParser/streamed_output/-",
                "value": ["bear"],
            }
        ),
        RunLogPatch(
            {"op": "add", "path": "/streamed_output/-", "value": ["bear"]},
            {"op": "replace", "path": "/final_output", "value": ["bear"]},
        ),
        RunLogPatch(
            {
                "op": "add",
                "path": "/logs/CommaSeparatedListOutputParser/streamed_output/-",
                "value": ["dog"],
            }
        ),
        RunLogPatch(
            {"op": "add", "path": "/streamed_output/-", "value": ["dog"]},
            {"op": "add", "path": "/final_output/1", "value": "dog"},
        ),
        RunLogPatch(
            {
                "op": "add",
                "path": "/logs/CommaSeparatedListOutputParser/streamed_output/-",
                "value": ["cat"],
            }
        ),
        RunLogPatch(
            {"op": "add", "path": "/streamed_output/-", "value": ["cat"]},
            {"op": "add", "path": "/final_output/2", "value": "cat"},
        ),
        RunLogPatch(
            {
                "op": "add",
                "path": "/logs/CommaSeparatedListOutputParser/final_output",
                "value": {"output": ["bear", "dog", "cat"]},
            },
            {
                "op": "add",
                "path": "/logs/CommaSeparatedListOutputParser/end_time",
                "value": "2023-01-01T00:00:00.000+00:00",
            },
        ),
    ]
    assert stream_log == expected