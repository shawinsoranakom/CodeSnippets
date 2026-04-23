async def get_client() -> AsyncGenerator[DummyClient, None]:
    client = DummyClient()
    yield client
    await client.close()