async def test_prompt_with_chat_model_async(
    mocker: MockerFixture,
    snapshot: SnapshotAssertion,
) -> None:
    prompt = (
        SystemMessagePromptTemplate.from_template("You are a nice assistant.")
        + "{question}"
    )
    chat = FakeListChatModel(responses=["foo"])

    chain = prompt | chat

    assert repr(chain) == snapshot
    assert isinstance(chain, RunnableSequence)
    assert chain.first == prompt
    assert chain.middle == []
    assert chain.last == chat
    assert dumps(chain, pretty=True) == snapshot

    # Test invoke
    prompt_spy = mocker.spy(prompt.__class__, "ainvoke")
    chat_spy = mocker.spy(chat.__class__, "ainvoke")
    tracer = FakeTracer()
    assert await chain.ainvoke(
        {"question": "What is your name?"}, {"callbacks": [tracer]}
    ) == _any_id_ai_message(content="foo")
    assert prompt_spy.call_args.args[1] == {"question": "What is your name?"}
    assert chat_spy.call_args.args[1] == ChatPromptValue(
        messages=[
            SystemMessage(content="You are a nice assistant."),
            HumanMessage(content="What is your name?"),
        ]
    )

    assert tracer.runs == snapshot

    mocker.stop(prompt_spy)
    mocker.stop(chat_spy)

    # Test batch
    prompt_spy = mocker.spy(prompt.__class__, "abatch")
    chat_spy = mocker.spy(chat.__class__, "abatch")
    tracer = FakeTracer()
    assert await chain.abatch(
        [
            {"question": "What is your name?"},
            {"question": "What is your favorite color?"},
        ],
        {"callbacks": [tracer]},
    ) == [
        _any_id_ai_message(content="foo"),
        _any_id_ai_message(content="foo"),
    ]
    assert prompt_spy.call_args.args[1] == [
        {"question": "What is your name?"},
        {"question": "What is your favorite color?"},
    ]
    assert chat_spy.call_args.args[1] == [
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
    assert (
        len(
            [
                r
                for r in tracer.runs
                if r.parent_run_id is None and len(r.child_runs) == 2
            ]
        )
        == 2
    ), "Each of 2 outer runs contains exactly two inner runs (1 prompt, 1 chat)"
    mocker.stop(prompt_spy)
    mocker.stop(chat_spy)

    # Test stream
    prompt_spy = mocker.spy(prompt.__class__, "ainvoke")
    chat_spy = mocker.spy(chat.__class__, "astream")
    tracer = FakeTracer()
    assert [
        a
        async for a in chain.astream(
            {"question": "What is your name?"}, {"callbacks": [tracer]}
        )
    ] == [
        _any_id_ai_message_chunk(content="f"),
        _any_id_ai_message_chunk(content="o"),
        _any_id_ai_message_chunk(content="o", chunk_position="last"),
    ]
    assert prompt_spy.call_args.args[1] == {"question": "What is your name?"}
    assert chat_spy.call_args.args[1] == ChatPromptValue(
        messages=[
            SystemMessage(content="You are a nice assistant."),
            HumanMessage(content="What is your name?"),
        ]
    )