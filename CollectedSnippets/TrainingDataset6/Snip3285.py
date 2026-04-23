async def read_optional_str(p: Annotated[str | None, Cookie()] = None):
    return {"p": p}