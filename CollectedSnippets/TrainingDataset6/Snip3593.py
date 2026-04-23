def read_model_optional_alias_and_validation_alias(
    p: Annotated[HeaderModelOptionalAliasAndValidationAlias, Header()],
):
    return {"p": p.p}