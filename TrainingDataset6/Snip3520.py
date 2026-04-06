def read_model_required_alias_and_validation_alias(
    p: Annotated[FormModelRequiredAliasAndValidationAlias, Form()],
):
    return {"p": p.p}