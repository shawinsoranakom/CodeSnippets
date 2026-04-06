async def read_model_required_list_alias(
    p: Annotated[QueryModelRequiredListAlias, Query()],
):
    return {"p": p.p}