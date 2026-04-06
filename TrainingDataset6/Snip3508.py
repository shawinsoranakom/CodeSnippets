async def read_model_required_alias(p: Annotated[FormModelRequiredAlias, Form()]):
    return {"p": p.p}