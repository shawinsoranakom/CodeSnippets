def test_runnable_iter_context_config() -> None:
    """Test generator runnable config propagation.

    Test that a generator can call other runnables with config
    propagated from the context.
    """
    fake = RunnableLambda(len)

    @chain
    def gen(value: str) -> Iterator[int]:
        yield fake.invoke(value)
        yield fake.invoke(value * 2)
        yield fake.invoke(value * 3)

    assert gen.get_input_jsonschema() == {
        "title": "gen_input",
        "type": "string",
    }
    assert gen.get_output_jsonschema() == {
        "title": "gen_output",
        "type": "integer",
    }

    tracer = FakeTracer()
    assert gen.invoke("a", {"callbacks": [tracer]}) == 6
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    tracer.runs.clear()

    assert list(gen.stream("a")) == [1, 2, 3]
    assert len(tracer.runs) == 0, "callbacks doesn't persist from previous call"

    tracer = FakeTracer()
    assert list(gen.stream("a", {"callbacks": [tracer]})) == [1, 2, 3]
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]

    tracer = FakeTracer()
    assert gen.batch(["a", "a"], {"callbacks": [tracer]}) == [6, 6]
    assert len(tracer.runs) == 2
    assert tracer.runs[0].outputs == {"output": 6}
    assert tracer.runs[1].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    assert len(tracer.runs[1].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[1].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[1].child_runs] == [1, 2, 3]