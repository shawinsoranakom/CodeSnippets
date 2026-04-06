async def read_model_required_list_validation_alias(
    p: Annotated[QueryModelRequiredListValidationAlias, Query()],
):
    return {"p": p.p}