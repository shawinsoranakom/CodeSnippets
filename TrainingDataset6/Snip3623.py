async def read_required_str(p: Annotated[str, Path()]):
    return {"p": p}