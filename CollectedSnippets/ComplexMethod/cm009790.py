async def test_runnable_lambda_context_config_async() -> None:
    """Test function runnable config propagation.

    Test that a function can call other runnables with config
    propagated from the context.
    """
    fake = RunnableLambda(len)

    @chain
    async def afun(value: str) -> int:
        output = await fake.ainvoke(value)
        output += await fake.ainvoke(value * 2)
        output += await fake.ainvoke(value * 3)
        return output

    assert afun.get_input_jsonschema() == {"title": "afun_input", "type": "string"}
    assert afun.get_output_jsonschema() == {
        "title": "afun_output",
        "type": "integer",
    }

    tracer = FakeTracer()
    assert await afun.ainvoke("a", {"callbacks": [tracer]}) == 6
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    tracer.runs.clear()

    assert [p async for p in afun.astream("a")] == [6]
    assert len(tracer.runs) == 0, "callbacks doesn't persist from previous call"

    tracer = FakeTracer()
    assert [p async for p in afun.astream("a", {"callbacks": [tracer]})] == [6]
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]

    tracer = FakeTracer()
    assert await afun.abatch(["a", "a"], {"callbacks": [tracer]}) == [6, 6]
    assert len(tracer.runs) == 2
    assert tracer.runs[0].outputs == {"output": 6}
    assert tracer.runs[1].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    assert len(tracer.runs[1].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[1].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[1].child_runs] == [1, 2, 3]