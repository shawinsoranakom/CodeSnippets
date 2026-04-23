async def read_required_alias(p: Annotated[str, Query(alias="p_alias")]):
    return {"p": p}