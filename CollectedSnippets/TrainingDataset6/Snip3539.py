async def read_model_required_list_validation_alias(
    p: Annotated[HeaderModelRequiredListValidationAlias, Header()],
):
    return {"p": p.p}