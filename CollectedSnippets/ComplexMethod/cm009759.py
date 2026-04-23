def test_combining_sequences(
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

    prompt2 = (
        SystemMessagePromptTemplate.from_template("You are a nicer assistant.")
        + "{question}"
    )
    chat2 = FakeListChatModel(responses=["baz, qux"])
    parser2 = CommaSeparatedListOutputParser()
    input_formatter = RunnableLambda[list[str], dict[str, Any]](
        lambda x: {"question": x[0] + x[1]}
    )

    chain2 = input_formatter | prompt2 | chat2 | parser2

    assert isinstance(chain2, RunnableSequence)
    assert chain2.first == input_formatter
    assert chain2.middle == [prompt2, chat2]
    assert chain2.last == parser2
    assert dumps(chain2, pretty=True) == snapshot

    combined_chain = chain | chain2

    assert isinstance(combined_chain, RunnableSequence)
    assert combined_chain.first == prompt
    assert combined_chain.middle == [
        chat,
        parser,
        input_formatter,
        prompt2,
        chat2,
    ]
    assert combined_chain.last == parser2
    assert dumps(combined_chain, pretty=True) == snapshot

    # Test invoke
    tracer = FakeTracer()
    assert combined_chain.invoke(
        {"question": "What is your name?"}, {"callbacks": [tracer]}
    ) == ["baz", "qux"]

    assert tracer.runs == snapshot