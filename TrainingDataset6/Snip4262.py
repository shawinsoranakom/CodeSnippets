async def stream_events():
    yield {"msg": "hello"}
    yield {"msg": "world"}