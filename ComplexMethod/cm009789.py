def test_runnable_lambda_context_config() -> None:
    """Test function runnable config propagation.

    Test that a function can call other runnables with config
    propagated from the context.
    """
    fake = RunnableLambda(len)

    @chain
    def fun(value: str) -> int:
        output = fake.invoke(value)
        output += fake.invoke(value * 2)
        output += fake.invoke(value * 3)
        return output

    assert fun.get_input_jsonschema() == {"title": "fun_input", "type": "string"}
    assert fun.get_output_jsonschema() == {
        "title": "fun_output",
        "type": "integer",
    }

    tracer = FakeTracer()
    assert fun.invoke("a", {"callbacks": [tracer]}) == 6
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    tracer.runs.clear()

    assert list(fun.stream("a")) == [6]
    assert len(tracer.runs) == 0, "callbacks doesn't persist from previous call"

    tracer = FakeTracer()
    assert list(fun.stream("a", {"callbacks": [tracer]})) == [6]
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]

    tracer = FakeTracer()
    assert fun.batch(["a", "a"], {"callbacks": [tracer]}) == [6, 6]
    assert len(tracer.runs) == 2
    assert tracer.runs[0].outputs == {"output": 6}
    assert tracer.runs[1].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    assert len(tracer.runs[1].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[1].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[1].child_runs] == [1, 2, 3]