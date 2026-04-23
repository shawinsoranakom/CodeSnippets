async def test_prompt_with_llm_and_async_lambda(
    mocker: MockerFixture, snapshot: SnapshotAssertion
) -> None:
    prompt = (
        SystemMessagePromptTemplate.from_template("You are a nice assistant.")
        + "{question}"
    )
    llm = FakeListLLM(responses=["foo", "bar"])

    async def passthrough(value: Any) -> Any:
        return value

    chain = prompt | llm | passthrough

    assert isinstance(chain, RunnableSequence)
    assert chain.first == prompt
    assert chain.middle == [llm]
    assert chain.last == RunnableLambda(func=passthrough)
    assert dumps(chain, pretty=True) == snapshot

    # Test invoke
    prompt_spy = mocker.spy(prompt.__class__, "ainvoke")
    llm_spy = mocker.spy(llm.__class__, "ainvoke")
    tracer = FakeTracer()
    assert (
        await chain.ainvoke({"question": "What is your name?"}, {"callbacks": [tracer]})
        == "foo"
    )
    assert prompt_spy.call_args.args[1] == {"question": "What is your name?"}
    assert llm_spy.call_args.args[1] == ChatPromptValue(
        messages=[
            SystemMessage(content="You are a nice assistant."),
            HumanMessage(content="What is your name?"),
        ]
    )
    assert tracer.runs == snapshot
    mocker.stop(prompt_spy)
    mocker.stop(llm_spy)