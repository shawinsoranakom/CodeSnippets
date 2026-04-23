async def test_runnable_iter_context_config_async() -> None:
    """Test generator runnable config propagation.

    Test that a generator can call other runnables with config
    propagated from the context.
    """
    fake = RunnableLambda(len)

    @chain
    async def agen(value: str) -> AsyncIterator[int]:
        yield await fake.ainvoke(value)
        yield await fake.ainvoke(value * 2)
        yield await fake.ainvoke(value * 3)

    assert agen.get_input_jsonschema() == {
        "title": "agen_input",
        "type": "string",
    }
    assert agen.get_output_jsonschema() == {
        "title": "agen_output",
        "type": "integer",
    }

    tracer = FakeTracer()
    assert await agen.ainvoke("a", {"callbacks": [tracer]}) == 6
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    tracer.runs.clear()

    assert [p async for p in agen.astream("a")] == [1, 2, 3]
    assert len(tracer.runs) == 0, "callbacks doesn't persist from previous call"

    tracer = FakeTracer()
    assert [p async for p in agen.astream("a", {"callbacks": [tracer]})] == [
        1,
        2,
        3,
    ]
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]

    tracer = FakeTracer()
    assert [p async for p in agen.astream_log("a", {"callbacks": [tracer]})]
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]

    tracer = FakeTracer()
    assert await agen.abatch(["a", "a"], {"callbacks": [tracer]}) == [6, 6]
    assert len(tracer.runs) == 2
    assert tracer.runs[0].outputs == {"output": 6}
    assert tracer.runs[1].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    assert len(tracer.runs[1].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[1].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[1].child_runs] == [1, 2, 3]