def test_runnable_gen_context_config() -> None:
    """Test generator runnable config propagation.

    Test that a generator can call other runnables with config
    propagated from the context.
    """
    fake = RunnableLambda(len)

    def gen(_: Iterator[Any]) -> Iterator[int]:
        yield fake.invoke("a")
        yield fake.invoke("aa")
        yield fake.invoke("aaa")

    runnable = RunnableGenerator(gen)

    assert runnable.get_input_jsonschema() == {"title": "gen_input"}
    assert runnable.get_output_jsonschema() == {
        "title": "gen_output",
        "type": "integer",
    }

    tracer = FakeTracer()
    run_id = uuid.uuid4()
    assert runnable.invoke(None, {"callbacks": [tracer], "run_id": run_id}) == 6
    assert len(tracer.runs) == 1
    assert tracer.runs[0].outputs == {"output": 6}
    assert len(tracer.runs[0].child_runs) == 3
    assert [r.inputs["input"] for r in tracer.runs[0].child_runs] == ["a", "aa", "aaa"]
    assert [(r.outputs or {})["output"] for r in tracer.runs[0].child_runs] == [1, 2, 3]
    run_ids = tracer.run_ids
    assert run_id in run_ids
    assert len(run_ids) == len(set(run_ids))
    tracer.runs.clear()

    assert list(runnable.stream(None)) == [1, 2, 3]
    assert len(tracer.runs) == 0, "callbacks doesn't persist from previous call"

    tracer = FakeTracer()
    run_id = uuid.uuid4()
    assert list(runnable.stream(None, {"callbacks": [tracer], "run_id": run_id})) == [
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
    tracer.runs.clear()

    tracer = FakeTracer()
    run_id = uuid.uuid4()

    with pytest.warns(RuntimeWarning):
        assert runnable.batch(
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