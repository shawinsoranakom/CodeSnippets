async def read_required_str(p: Annotated[str, Body(embed=True)]):
    return {"p": p}