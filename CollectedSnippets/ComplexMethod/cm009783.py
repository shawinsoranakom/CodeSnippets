async def test_runnable_branch_astream_with_callbacks() -> None:
    """Verify that astream works for RunnableBranch when using callbacks."""
    tracer = FakeTracer()

    def raise_value_error(x: str) -> Any:
        """Raise a value error."""
        msg = f"x is {x}"
        raise ValueError(msg)

    llm_res = "i'm a textbot"
    # sleep to better simulate a real stream
    llm = FakeStreamingListLLM(responses=[llm_res], sleep=0.01)

    branch = RunnableBranch[str, Any](
        (lambda x: x == "error", raise_value_error),
        (lambda x: x == "hello", llm),
        lambda x: x,
    )
    config: RunnableConfig = {"callbacks": [tracer]}

    assert [_ async for _ in branch.astream("hello", config=config)] == list(llm_res)

    assert len(tracer.runs) == 1
    assert tracer.runs[0].error is None
    assert tracer.runs[0].outputs == {"output": llm_res}

    # Verify that the chain on error is invoked
    with pytest.raises(ValueError, match="x is error"):
        _ = [_ async for _ in branch.astream("error", config=config)]

    assert len(tracer.runs) == 2
    assert "ValueError('x is error')" in str(tracer.runs[1].error)
    assert not tracer.runs[1].outputs

    assert [_ async for _ in branch.astream("bye", config=config)] == ["bye"]

    assert len(tracer.runs) == 3
    assert tracer.runs[2].error is None
    assert tracer.runs[2].outputs == {"output": "bye"}