def read_model_required_alias_and_validation_alias(
    p: Annotated[HeaderModelRequiredAliasAndValidationAlias, Header()],
):
    return {"p": p.p}