async def is_strong_enough(chat_model, embedding_model):
    count = settings.STRONG_TEST_COUNT
    if not chat_model or not embedding_model:
        return
    if isinstance(count, int) and count <= 0:
        return

    @timeout(60, 2)
    async def _is_strong_enough():
        nonlocal chat_model, embedding_model
        if embedding_model:
            await asyncio.wait_for(
                thread_pool_exec(embedding_model.encode, ["Are you strong enough!?"]),
                timeout=10
            )

        if chat_model:
            res = await asyncio.wait_for(
                chat_model.async_chat("Nothing special.", [{"role": "user", "content": "Are you strong enough!?"}]),
                timeout=30
            )
            if "**ERROR**" in res:
                raise Exception(res)

    # Pressure test for GraphRAG task
    tasks = [
        asyncio.create_task(_is_strong_enough())
        for _ in range(count)
    ]
    try:
        await asyncio.gather(*tasks, return_exceptions=False)
    except Exception as e:
        logging.error(f"Pressure test failed: {e}")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise