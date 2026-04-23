def stream_items_invalid_sync() -> Iterable[Item]:
    yield {"name": "valid", "price": 1.0}
    yield {"name": "invalid", "price": "not-a-number"}