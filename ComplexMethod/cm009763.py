def test_higher_order_lambda_runnable(
    mocker: MockerFixture, snapshot: SnapshotAssertion
) -> None:
    math_chain = ChatPromptTemplate.from_template(
        "You are a math genius. Answer the question: {question}"
    ) | FakeListLLM(responses=["4"])
    english_chain = ChatPromptTemplate.from_template(
        "You are an english major. Answer the question: {question}"
    ) | FakeListLLM(responses=["2"])
    input_map = RunnableParallel(
        key=lambda x: x["key"],
        input={"question": lambda x: x["question"]},
    )

    def router(params: dict[str, Any]) -> Runnable:
        if params["key"] == "math":
            return itemgetter("input") | math_chain
        if params["key"] == "english":
            return itemgetter("input") | english_chain
        msg = f"Unknown key: {params['key']}"
        raise ValueError(msg)

    chain: Runnable = input_map | router
    assert dumps(chain, pretty=True) == snapshot

    result = chain.invoke({"key": "math", "question": "2 + 2"})
    assert result == "4"

    result2 = chain.batch(
        [
            {"key": "math", "question": "2 + 2"},
            {"key": "english", "question": "2 + 2"},
        ]
    )
    assert result2 == ["4", "2"]

    # Test invoke
    math_spy = mocker.spy(math_chain.__class__, "invoke")
    tracer = FakeTracer()
    assert (
        chain.invoke({"key": "math", "question": "2 + 2"}, {"callbacks": [tracer]})
        == "4"
    )
    assert math_spy.call_args.args[1] == {
        "key": "math",
        "input": {"question": "2 + 2"},
    }
    assert len([r for r in tracer.runs if r.parent_run_id is None]) == 1
    parent_run = next(r for r in tracer.runs if r.parent_run_id is None)
    assert len(parent_run.child_runs) == 2
    router_run = parent_run.child_runs[1]
    assert router_run.name == "router"
    assert len(router_run.child_runs) == 1
    math_run = router_run.child_runs[0]
    assert math_run.name == "RunnableSequence"
    assert len(math_run.child_runs) == 3