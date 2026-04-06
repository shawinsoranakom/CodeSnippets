async def read_optional_alias(
    p: Annotated[str | None, Cookie(alias="p_alias")] = None,
):
    return {"p": p}