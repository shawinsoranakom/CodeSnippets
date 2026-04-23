async def read_optional_str(p: Annotated[str | None, Body(embed=True)] = None):
    return {"p": p}