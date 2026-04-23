async def read_required_alias(
    p: Annotated[str, Body(embed=True, alias="p_alias")],
):
    return {"p": p}