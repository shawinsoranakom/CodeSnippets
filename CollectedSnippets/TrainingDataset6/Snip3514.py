def read_model_required_validation_alias(
    p: Annotated[FormModelRequiredValidationAlias, Form()],
):
    return {"p": p.p}