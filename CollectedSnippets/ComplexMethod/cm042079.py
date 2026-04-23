async def test_subscription_run():
    callback_done = 0

    async def trigger():
        while True:
            yield Message(content="the latest news about OpenAI")
            await asyncio.sleep(3600 * 24)

    class MockRole(Role):
        async def run(self, message=None):
            return Message(content="")

    async def callback(message):
        nonlocal callback_done
        callback_done += 1

    runner = SubscriptionRunner()

    roles = []
    for _ in range(2):
        role = MockRole()
        roles.append(role)
        await runner.subscribe(role, trigger(), callback)

    task = asyncio.get_running_loop().create_task(runner.run())

    for _ in range(10):
        if callback_done == 2:
            break
        await asyncio.sleep(0)
    else:
        raise TimeoutError("callback not call")

    role = roles[0]
    assert role in runner.tasks
    await runner.unsubscribe(roles[0])

    for _ in range(10):
        if role not in runner.tasks:
            break
        await asyncio.sleep(0)
    else:
        raise TimeoutError("callback not call")

    task.cancel()
    for i in runner.tasks.values():
        i.cancel()