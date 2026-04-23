def read_model_required_alias_and_validation_alias(
    p: Annotated[QueryModelRequiredAliasAndValidationAlias, Query()],
):
    return {"p": p.p}