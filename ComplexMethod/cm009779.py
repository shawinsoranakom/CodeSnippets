def test_runnable_branch_invoke_call_counts(mocker: MockerFixture) -> None:
    """Verify that runnables are invoked only when necessary."""
    # Test with single branch
    add = RunnableLambda[int, int](lambda x: x + 1)
    sub = RunnableLambda[int, int](lambda x: x - 1)
    condition = RunnableLambda[int, bool](lambda x: x > 0)
    spy = mocker.spy(condition, "invoke")
    add_spy = mocker.spy(add, "invoke")

    branch = RunnableBranch[int, int]((condition, add), (condition, add), sub)
    assert spy.call_count == 0
    assert add_spy.call_count == 0

    assert branch.invoke(1) == 2
    assert add_spy.call_count == 1
    assert spy.call_count == 1

    assert branch.invoke(2) == 3
    assert spy.call_count == 2
    assert add_spy.call_count == 2

    assert branch.invoke(-3) == -4
    # Should fall through to default branch with condition being evaluated twice!
    assert spy.call_count == 4
    # Add should not be invoked
    assert add_spy.call_count == 2