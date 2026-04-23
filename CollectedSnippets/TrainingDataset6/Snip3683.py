async def read_model_optional_alias(p: Annotated[QueryModelOptionalAlias, Query()]):
    return {"p": p.p}