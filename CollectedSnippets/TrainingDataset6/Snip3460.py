async def read_model_optional_list_alias(
    p: Annotated[FormModelOptionalListAlias, Form()],
):
    return {"p": p.p}