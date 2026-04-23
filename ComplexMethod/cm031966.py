def iter_many(items, onempty=None):
    if not items:
        if onempty is None:
            return
        if not callable(onempty):
            raise onEmpty
        items = onempty(items)
        yield from iter_many(items, onempty=None)
        return
    items = iter(items)
    try:
        first = next(items)
    except StopIteration:
        if onempty is None:
            return
        if not callable(onempty):
            raise onEmpty
        items = onempty(items)
        yield from iter_many(items, onempty=None)
    else:
        try:
            second = next(items)
        except StopIteration:
            yield first, False
            return
        else:
            yield first, True
            yield second, True
        for item in items:
            yield item, True