async def stream_items_invalid() -> AsyncIterable[Item]:
    yield {"name": "valid", "price": 1.0}
    yield {"name": "invalid", "price": "not-a-number"}