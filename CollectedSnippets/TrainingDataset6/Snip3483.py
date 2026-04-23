async def read_optional_alias(
    p: Annotated[str | None, Form(alias="p_alias")] = None,
):
    return {"p": p}