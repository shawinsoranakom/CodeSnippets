def test_seq_prompt_map(mocker: MockerFixture, snapshot: SnapshotAssertion) -> None:
    passthrough = mocker.Mock(side_effect=lambda x: x)

    prompt = (
        SystemMessagePromptTemplate.from_template("You are a nice assistant.")
        + "{question}"
    )

    chat = FakeListChatModel(responses=["i'm a chatbot"])

    llm = FakeListLLM(responses=["i'm a textbot"])

    chain = (
        prompt
        | passthrough
        | {
            "chat": chat.bind(stop=["Thought:"]),
            "llm": llm,
            "passthrough": passthrough,
        }
    )

    assert isinstance(chain, RunnableSequence)
    assert chain.first == prompt
    assert chain.middle == [RunnableLambda(passthrough)]
    assert isinstance(chain.last, RunnableParallel)

    if PYDANTIC_VERSION_AT_LEAST_210:
        assert dumps(chain, pretty=True) == snapshot

    # Test invoke
    prompt_spy = mocker.spy(prompt.__class__, "invoke")
    chat_spy = mocker.spy(chat.__class__, "invoke")
    llm_spy = mocker.spy(llm.__class__, "invoke")
    tracer = FakeTracer()
    assert chain.invoke(
        {"question": "What is your name?"}, {"callbacks": [tracer]}
    ) == {
        "chat": _any_id_ai_message(content="i'm a chatbot"),
        "llm": "i'm a textbot",
        "passthrough": ChatPromptValue(
            messages=[
                SystemMessage(content="You are a nice assistant."),
                HumanMessage(content="What is your name?"),
            ]
        ),
    }
    assert prompt_spy.call_args.args[1] == {"question": "What is your name?"}
    assert chat_spy.call_args.args[1] == ChatPromptValue(
        messages=[
            SystemMessage(content="You are a nice assistant."),
            HumanMessage(content="What is your name?"),
        ]
    )
    assert llm_spy.call_args.args[1] == ChatPromptValue(
        messages=[
            SystemMessage(content="You are a nice assistant."),
            HumanMessage(content="What is your name?"),
        ]
    )
    assert len([r for r in tracer.runs if r.parent_run_id is None]) == 1
    parent_run = next(r for r in tracer.runs if r.parent_run_id is None)
    assert len(parent_run.child_runs) == 3
    map_run = parent_run.child_runs[2]
    assert map_run.name == "RunnableParallel<chat,llm,passthrough>"
    assert len(map_run.child_runs) == 3