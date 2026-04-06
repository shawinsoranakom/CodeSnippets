async def read_optional_str(p: Annotated[str | None, Header()] = None):
    return {"p": p}