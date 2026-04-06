async def overrider_dependency_simple(q: str | None = None):
    return {"q": q, "skip": 5, "limit": 10}