async def read_required_str(p: Annotated[str, Cookie()]):
    return {"p": p}