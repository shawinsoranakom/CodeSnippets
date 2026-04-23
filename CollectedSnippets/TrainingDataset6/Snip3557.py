async def read_model_optional_list_alias(
    p: Annotated[HeaderModelOptionalListAlias, Header()],
):
    return {"p": p.p}