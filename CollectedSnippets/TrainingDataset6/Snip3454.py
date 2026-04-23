async def read_optional_list_str(
    p: Annotated[list[str] | None, Form()] = None,
):
    return {"p": p}