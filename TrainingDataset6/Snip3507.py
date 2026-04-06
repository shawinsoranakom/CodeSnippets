async def read_required_alias(p: Annotated[str, Form(alias="p_alias")]):
    return {"p": p}