def read_items(q: str | None = Param(default=None)):  # type: ignore
    return {"q": q}