def read_items(q: list[int] = Query(default=None)):
    return {"q": q}