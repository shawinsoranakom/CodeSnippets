async def read_optional_list_str(
    p: Annotated[list[str] | None, Header()] = None,
):
    return {"p": p}