async def read_required_alias(p: Annotated[str, Header(alias="p_alias")]):
    return {"p": p}