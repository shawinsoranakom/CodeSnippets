async def read_model_required_list_alias(
    p: Annotated[FormModelRequiredListAlias, Form()],
):
    return {"p": p.p}