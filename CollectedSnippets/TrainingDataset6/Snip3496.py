def read_model_optional_alias_and_validation_alias(
    p: Annotated[FormModelOptionalAliasAndValidationAlias, Form()],
):
    return {"p": p.p}