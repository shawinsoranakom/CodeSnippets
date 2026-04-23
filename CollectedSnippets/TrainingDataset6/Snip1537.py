def stream_items_no_async() -> Iterable[Item]:
    for item in items:
        yield item