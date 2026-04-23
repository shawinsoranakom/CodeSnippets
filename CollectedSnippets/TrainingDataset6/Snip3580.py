async def read_optional_alias(
    p: Annotated[str | None, Header(alias="p_alias")] = None,
):
    return {"p": p}