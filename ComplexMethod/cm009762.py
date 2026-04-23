def test_router_runnable(mocker: MockerFixture, snapshot: SnapshotAssertion) -> None:
    chain1 = ChatPromptTemplate.from_template(
        "You are a math genius. Answer the question: {question}"
    ) | FakeListLLM(responses=["4"])
    chain2 = ChatPromptTemplate.from_template(
        "You are an english major. Answer the question: {question}"
    ) | FakeListLLM(responses=["2"])
    router = RouterRunnable({"math": chain1, "english": chain2})
    chain: Runnable = {
        "key": lambda x: x["key"],
        "input": {"question": lambda x: x["question"]},
    } | router
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
    router_spy = mocker.spy(router.__class__, "invoke")
    tracer = FakeTracer()
    assert (
        chain.invoke({"key": "math", "question": "2 + 2"}, {"callbacks": [tracer]})
        == "4"
    )
    assert router_spy.call_args.args[1] == {
        "key": "math",
        "input": {"question": "2 + 2"},
    }
    assert len([r for r in tracer.runs if r.parent_run_id is None]) == 1
    parent_run = next(r for r in tracer.runs if r.parent_run_id is None)
    assert len(parent_run.child_runs) == 2
    router_run = parent_run.child_runs[1]
    assert router_run.name == "RunnableSequence"  # TODO: should be RunnableRouter
    assert len(router_run.child_runs) == 2