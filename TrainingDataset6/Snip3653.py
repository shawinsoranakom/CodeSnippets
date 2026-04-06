async def read_optional_list_str(
    p: Annotated[list[str] | None, Query()] = None,
):
    return {"p": p}