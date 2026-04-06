async def read_optional_list_str(
    p: Annotated[list[str] | None, Body(embed=True)] = None,
):
    return {"p": p}