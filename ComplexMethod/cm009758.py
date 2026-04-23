def test_prompt_with_chat_model_and_parser(
    mocker: MockerFixture,
    snapshot: SnapshotAssertion,
) -> None:
    prompt = (
        SystemMessagePromptTemplate.from_template("You are a nice assistant.")
        + "{question}"
    )
    chat = FakeListChatModel(responses=["foo, bar"])
    parser = CommaSeparatedListOutputParser()

    chain = prompt | chat | parser

    assert isinstance(chain, RunnableSequence)
    assert chain.first == prompt
    assert chain.middle == [chat]
    assert chain.last == parser
    assert dumps(chain, pretty=True) == snapshot

    # Test invoke
    prompt_spy = mocker.spy(prompt.__class__, "invoke")
    chat_spy = mocker.spy(chat.__class__, "invoke")
    parser_spy = mocker.spy(parser.__class__, "invoke")
    tracer = FakeTracer()
    assert chain.invoke(
        {"question": "What is your name?"}, {"callbacks": [tracer]}
    ) == ["foo", "bar"]
    assert prompt_spy.call_args.args[1] == {"question": "What is your name?"}
    assert chat_spy.call_args.args[1] == ChatPromptValue(
        messages=[
            SystemMessage(content="You are a nice assistant."),
            HumanMessage(content="What is your name?"),
        ]
    )
    assert parser_spy.call_args.args[1] == _any_id_ai_message(content="foo, bar")

    assert tracer.runs == snapshot