async def test_runnable_lambda_astream_with_callbacks() -> None:
    """Test that astream works for RunnableLambda when using callbacks."""
    tracer = FakeTracer()

    llm_res = "i'm a textbot"
    # sleep to better simulate a real stream
    llm = FakeStreamingListLLM(responses=[llm_res], sleep=0.01)
    config: RunnableConfig = {"callbacks": [tracer]}

    assert [
        _
        async for _ in RunnableLambda[str, str](lambda _: llm).astream(
            "", config=config
        )
    ] == list(llm_res)

    assert len(tracer.runs) == 1
    assert tracer.runs[0].error is None
    assert tracer.runs[0].outputs == {"output": llm_res}

    def raise_value_error(_: int) -> int:
        """Raise a value error."""
        msg = "x is too large"
        raise ValueError(msg)

    # Check that the chain on error is invoked
    with pytest.raises(ValueError, match="x is too large"):
        _ = [
            _
            async for _ in RunnableLambda(raise_value_error).astream(
                1000, config=config
            )
        ]

    assert len(tracer.runs) == 2
    assert "ValueError('x is too large')" in str(tracer.runs[1].error)
    assert not tracer.runs[1].outputs