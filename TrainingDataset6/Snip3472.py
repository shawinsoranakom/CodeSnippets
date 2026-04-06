def read_model_optional_list_alias_and_validation_alias(
    p: Annotated[FormModelOptionalListAliasAndValidationAlias, Form()],
):
    return {"p": p.p}