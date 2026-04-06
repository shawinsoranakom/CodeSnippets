async def read_required_list_alias(p: Annotated[list[str], Query(alias="p_alias")]):
    return {"p": p}