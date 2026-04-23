async def b(dep: Dep[B]):
    return {"cls": dep.__class__.__name__}