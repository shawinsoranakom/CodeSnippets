async def test_higher_order_lambda_runnable_async(mocker: MockerFixture) -> None:
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

    def router(value: dict[str, Any]) -> Runnable:
        if value["key"] == "math":
            return itemgetter("input") | math_chain
        if value["key"] == "english":
            return itemgetter("input") | english_chain
        msg = f"Unknown key: {value['key']}"
        raise ValueError(msg)

    chain: Runnable = input_map | router

    result = await chain.ainvoke({"key": "math", "question": "2 + 2"})
    assert result == "4"

    result2 = await chain.abatch(
        [
            {"key": "math", "question": "2 + 2"},
            {"key": "english", "question": "2 + 2"},
        ]
    )
    assert result2 == ["4", "2"]

    # Test ainvoke
    async def arouter(params: dict[str, Any]) -> Runnable:
        if params["key"] == "math":
            return itemgetter("input") | math_chain
        if params["key"] == "english":
            return itemgetter("input") | english_chain
        msg = f"Unknown key: {params['key']}"
        raise ValueError(msg)

    achain: Runnable = input_map | arouter
    math_spy = mocker.spy(math_chain.__class__, "ainvoke")
    tracer = FakeTracer()
    assert (
        await achain.ainvoke(
            {"key": "math", "question": "2 + 2"}, {"callbacks": [tracer]}
        )
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
    assert router_run.name == "arouter"
    assert len(router_run.child_runs) == 1
    math_run = router_run.child_runs[0]
    assert math_run.name == "RunnableSequence"
    assert len(math_run.child_runs) == 3