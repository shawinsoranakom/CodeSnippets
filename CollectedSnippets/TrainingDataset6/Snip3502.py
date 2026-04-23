async def read_required_str(p: Annotated[str, Form()]):
    return {"p": p}