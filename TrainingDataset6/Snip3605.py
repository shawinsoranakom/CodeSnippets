async def read_model_required_alias(p: Annotated[HeaderModelRequiredAlias, Header()]):
    return {"p": p.p}