def read_model_required_validation_alias(
    p: Annotated[HeaderModelRequiredValidationAlias, Header()],
):
    return {"p": p.p}