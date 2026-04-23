async def test_async_retrying(mocker: MockerFixture) -> None:
    def _lambda(x: int) -> int:
        if x == 1:
            msg = "x is 1"
            raise ValueError(msg)
        if x == 2:
            msg = "x is 2"
            raise RuntimeError(msg)
        return x

    lambda_mock = mocker.Mock(side_effect=_lambda)
    runnable = RunnableLambda(lambda_mock)

    with pytest.raises(ValueError, match="x is 1"):
        await runnable.ainvoke(1)

    assert lambda_mock.call_count == 1
    lambda_mock.reset_mock()

    with pytest.raises(ValueError, match="x is 1"):
        await runnable.with_retry(
            stop_after_attempt=2,
            wait_exponential_jitter=False,
            retry_if_exception_type=(ValueError, KeyError),
        ).ainvoke(1)

    assert lambda_mock.call_count == 2  # retried
    lambda_mock.reset_mock()

    with pytest.raises(RuntimeError):
        await runnable.with_retry(
            stop_after_attempt=2,
            wait_exponential_jitter=False,
            retry_if_exception_type=(ValueError,),
        ).ainvoke(2)

    assert lambda_mock.call_count == 1  # did not retry
    lambda_mock.reset_mock()

    with pytest.raises(ValueError, match="x is 1"):
        await runnable.with_retry(
            stop_after_attempt=2,
            wait_exponential_jitter=False,
            retry_if_exception_type=(ValueError,),
        ).abatch([1, 2, 0])

    # 3rd input isn't retried because it succeeded
    assert lambda_mock.call_count == 3 + 2
    lambda_mock.reset_mock()

    output = await runnable.with_retry(
        stop_after_attempt=2,
        wait_exponential_jitter=False,
        retry_if_exception_type=(ValueError,),
    ).abatch([1, 2, 0], return_exceptions=True)

    # 3rd input isn't retried because it succeeded
    assert lambda_mock.call_count == 3 + 2
    assert len(output) == 3
    assert isinstance(output[0], ValueError)
    assert isinstance(output[1], RuntimeError)
    assert output[2] == 0
    lambda_mock.reset_mock()