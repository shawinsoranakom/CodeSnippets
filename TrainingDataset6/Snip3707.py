async def read_model_required_alias(p: Annotated[QueryModelRequiredAlias, Query()]):
    return {"p": p.p}