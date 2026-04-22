async def tick_runtime_loop() -> None:
        """Sleep just long enough to guarantee that the Runtime's loop
        has a chance to run.
        """
        # Our sleep time needs to be longer than the longest sleep time inside the
        # Runtime loop, which is 0.01 + (1 tick * number of connected sessions).
        # 0.03 is near-instant, and conservative enough that the tick will happen
        # under our test circumstances.
        await asyncio.sleep(0.03)