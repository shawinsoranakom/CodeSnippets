async def read_optional_str(p: Annotated[str | None, Form()] = None):
    return {"p": p}