async def read_optional_alias(
    p: Annotated[str | None, Body(embed=True, alias="p_alias")] = None,
):
    return {"p": p}