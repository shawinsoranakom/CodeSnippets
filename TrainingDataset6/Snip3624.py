async def read_required_alias(p: Annotated[str, Path(alias="p_alias")]):
    return {"p": p}