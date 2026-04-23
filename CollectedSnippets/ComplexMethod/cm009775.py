async def test_runnable_lambda_astream() -> None:
    """Test that astream works for both normal functions & those returning Runnable."""

    # Wrapper to make a normal function async
    def awrapper(func: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
        async def afunc(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return afunc

    # Normal output should work
    output: list[Any] = [
        chunk
        async for chunk in RunnableLambda(
            func=id,
            afunc=awrapper(range),  # id func is just dummy
        ).astream(5)
    ]
    assert output == [range(5)]

    # Normal output using func should also work
    output = [_ async for _ in RunnableLambda(range).astream(5)]
    assert output == [range(5)]

    # Runnable output should also work
    llm_res = "i'm a textbot"
    # sleep to better simulate a real stream
    llm = FakeStreamingListLLM(responses=[llm_res], sleep=0.01)

    output = [
        _
        async for _ in RunnableLambda(
            func=id,
            afunc=awrapper(lambda _: llm),
        ).astream("")
    ]
    assert output == list(llm_res)

    output = [
        chunk async for chunk in RunnableLambda[str, str](lambda _: llm).astream("")
    ]
    assert output == list(llm_res)