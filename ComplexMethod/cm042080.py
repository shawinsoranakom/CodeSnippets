async def test_subscription_run_error(loguru_caplog):
    async def trigger1():
        while True:
            yield Message(content="the latest news about OpenAI")
            await asyncio.sleep(3600 * 24)

    async def trigger2():
        yield Message(content="the latest news about OpenAI")

    class MockRole1(Role):
        async def run(self, message=None):
            raise RuntimeError

    class MockRole2(Role):
        async def run(self, message=None):
            return Message(content="")

    async def callback(msg: Message):
        print(msg)

    runner = SubscriptionRunner()
    await runner.subscribe(MockRole1(), trigger1(), callback)
    with pytest.raises(RuntimeError):
        await runner.run()

    await runner.subscribe(MockRole2(), trigger2(), callback)
    task = asyncio.get_running_loop().create_task(runner.run(False))

    for _ in range(10):
        if not runner.tasks:
            break
        await asyncio.sleep(0)
    else:
        raise TimeoutError("wait runner tasks empty timeout")

    task.cancel()
    for i in runner.tasks.values():
        i.cancel()
    assert len(loguru_caplog.records) >= 2
    logs = "".join(loguru_caplog.messages)
    assert "run error" in logs
    assert "has completed" in logs