def read_model_optional_list_alias_and_validation_alias(
    p: Annotated[HeaderModelOptionalListAliasAndValidationAlias, Header()],
):
    return {"p": p.p}