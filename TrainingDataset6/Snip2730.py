async def a(dep: Dep[A]):
    return {"cls": dep.__class__.__name__}