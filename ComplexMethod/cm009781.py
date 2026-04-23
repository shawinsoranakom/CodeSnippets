async def test_runnable_branch_ainvoke_callbacks() -> None:
    """Verify that callbacks are invoked correctly in ainvoke."""
    tracer = FakeTracer()

    async def raise_value_error(_: int) -> int:
        """Raise a value error."""
        msg = "x is too large"
        raise ValueError(msg)

    branch = RunnableBranch[int, int](
        (lambda x: x > 100, raise_value_error),
        lambda x: x - 1,
    )

    assert await branch.ainvoke(1, config={"callbacks": [tracer]}) == 0
    assert len(tracer.runs) == 1
    assert tracer.runs[0].error is None
    assert tracer.runs[0].outputs == {"output": 0}

    # Check that the chain on end is invoked
    with pytest.raises(ValueError, match="x is too large"):
        await branch.ainvoke(1000, config={"callbacks": [tracer]})

    assert len(tracer.runs) == 2
    assert "ValueError('x is too large')" in str(tracer.runs[1].error)
    assert not tracer.runs[1].outputs