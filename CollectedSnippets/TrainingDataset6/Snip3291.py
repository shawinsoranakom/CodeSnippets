async def read_model_optional_alias(p: Annotated[CookieModelOptionalAlias, Cookie()]):
    return {"p": p.p}