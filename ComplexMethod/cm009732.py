async def test_break_astream_events() -> None:
    class AwhileMaker:
        def __init__(self) -> None:
            self.reset()

        async def __call__(self, value: Any) -> Any:
            self.started = True
            try:
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                self.cancelled = True
                raise
            return value

        def reset(self) -> None:
            self.started = False
            self.cancelled = False

    alittlewhile = AwhileMaker()
    awhile = AwhileMaker()
    anotherwhile = AwhileMaker()

    outer_cancelled = False

    @chain
    async def sequence(value: Any) -> Any:
        try:
            yield await alittlewhile(value)
            yield await awhile(value)
            yield await anotherwhile(value)
        except asyncio.CancelledError:
            nonlocal outer_cancelled
            outer_cancelled = True
            raise

    # test interrupting astream_events v2

    got_event = False
    thread2: RunnableConfig = {"configurable": {"thread_id": 2}}
    async with aclosing(
        sequence.astream_events({"value": 1}, thread2, version="v2")
    ) as stream:
        async for chunk in stream:
            if chunk["event"] == "on_chain_stream":
                got_event = True
                assert chunk["data"]["chunk"] == {"value": 1}
                break

    # did break
    assert got_event
    # did cancel outer chain
    assert outer_cancelled

    # node "alittlewhile" starts, not cancelled
    assert alittlewhile.started is True
    assert alittlewhile.cancelled is False

    # node "awhile" starts but is cancelled
    assert awhile.started is True
    assert awhile.cancelled is True

    # node "anotherwhile" should never start
    assert anotherwhile.started is False