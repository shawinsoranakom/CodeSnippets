async def read_required_str(p: Annotated[str, Header()]):
    return {"p": p}