def read_model_optional_alias_and_validation_alias(
    p: Annotated[QueryModelOptionalAliasAndValidationAlias, Query()],
):
    return {"p": p.p}