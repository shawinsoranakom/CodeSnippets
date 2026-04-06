async def read_model_optional_alias(p: Annotated[HeaderModelOptionalAlias, Header()]):
    return {"p": p.p}