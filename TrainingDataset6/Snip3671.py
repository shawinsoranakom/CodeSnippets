def read_model_optional_list_alias_and_validation_alias(
    p: Annotated[QueryModelOptionalListAliasAndValidationAlias, Query()],
):
    return {"p": p.p}