async def read_model_optional_alias(p: Annotated[FormModelOptionalAlias, Form()]):
    return {"p": p.p}