async def read_required_alias(p: Annotated[str, Cookie(alias="p_alias")]):
    return {"p": p}