async def receive():  # type: ignore[no-untyped-def]
        # Simulate a client that never disconnects, rely on cancellation
        await anyio.sleep(float("inf"))
        return {"type": "http.disconnect"}