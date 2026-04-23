async def read_model_required_alias(p: Annotated[CookieModelRequiredAlias, Cookie()]):
    return {"p": p.p}