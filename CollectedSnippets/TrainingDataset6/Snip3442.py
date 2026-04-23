async def read_model_required_list_validation_alias(
    p: Annotated[FormModelRequiredListValidationAlias, Form()],
):
    return {"p": p.p}