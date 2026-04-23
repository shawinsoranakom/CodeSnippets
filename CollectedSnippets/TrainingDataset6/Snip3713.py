def read_model_required_validation_alias(
    p: Annotated[QueryModelRequiredValidationAlias, Query()],
):
    return {"p": p.p}