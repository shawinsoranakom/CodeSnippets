async def test_runnable_gen_context_config_async() -> None:
    """Test generator runnable config propagation.

    Test that a generator can call other runnables with config
    propagated from the context.
    """
    fake = RunnableLambda(len)

    async def agen(_: AsyncIterator[Any]) -> AsyncIterator[int]:
        yield await fake.ainvoke("a")
        yield await fake.ainvoke("aa")
        yield await fake.ainvoke("aaa")

    arunnable = RunnableGenerator(agen)

    tracer = FakeTracer()

    run_id = uuid.uuid4()
    assert await arunnable.ainvoke(None, {"callbacks": [tracer], "run_id": run_id}) == 6
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    run_ids = tracer.run_ids
    assert run_id in run_ids
    assert len(run_ids) == len(set(run_ids))
    tracer.runs.clear()

    assert [p async for p in arunnable.astream(None)] == [1, 2, 3]
    assert len(tracer.runs) == 0, "callbacks doesn't persist from previous call"

    tracer = FakeTracer()
    run_id = uuid.uuid4()
    assert [
        p
        async for p in arunnable.astream(
            None, {"callbacks": [tracer], "run_id": run_id}
        )
    ] == [
        1,
        2,
        3,
    ]
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    run_ids = tracer.run_ids
    assert run_id in run_ids
    assert len(run_ids) == len(set(run_ids))

    tracer = FakeTracer()
    run_id = uuid.uuid4()
    with pytest.warns(RuntimeWarning):
        assert await arunnable.abatch(
            [None, None], {"callbacks": [tracer], "run_id": run_id}
        ) == [6, 6]
    assert len(tracer.runs) == 2
    assert tracer.runs[0].outputs == {"output": 6}
    assert tracer.runs[1].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    assert len(tracer.runs[1].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[1].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[1].child_runs] == [1, 2, 3]