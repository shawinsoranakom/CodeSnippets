async def read_optional_list_alias(
    p: Annotated[list[str] | None, Query(alias="p_alias")] = None,
):
    return {"p": p}