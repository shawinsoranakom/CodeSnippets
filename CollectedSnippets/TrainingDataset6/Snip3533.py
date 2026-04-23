async def read_model_required_list_alias(
    p: Annotated[HeaderModelRequiredListAlias, Header()],
):
    return {"p": p.p}