async def read_model_optional_list_alias(
    p: Annotated[QueryModelOptionalListAlias, Query()],
):
    return {"p": p.p}