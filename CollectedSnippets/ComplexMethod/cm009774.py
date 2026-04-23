def test_runnable_lambda_stream_with_callbacks() -> None:
    """Test that stream works for RunnableLambda when using callbacks."""
    tracer = FakeTracer()

    llm_res = "i'm a textbot"
    # sleep to better simulate a real stream
    llm = FakeStreamingListLLM(responses=[llm_res], sleep=0.01)
    config: RunnableConfig = {"callbacks": [tracer]}

    assert list(
        RunnableLambda[str, str](lambda _: llm).stream("", config=config)
    ) == list(llm_res)

    assert len(tracer.runs) == 1
    assert tracer.runs[0].error is None
    assert tracer.runs[0].outputs == {"output": llm_res}

    def raise_value_error(_: int) -> int:
        """Raise a value error."""
        msg = "x is too large"
        raise ValueError(msg)

    # Check that the chain on error is invoked
    with pytest.raises(ValueError, match="x is too large"):
        _ = list(RunnableLambda(raise_value_error).stream(1000, config=config))

    assert len(tracer.runs) == 2
    assert "ValueError('x is too large')" in str(tracer.runs[1].error)
    assert not tracer.runs[1].outputs