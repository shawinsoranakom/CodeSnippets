def read_model_required_list_alias_and_validation_alias(
    p: Annotated[QueryModelRequiredListAliasAndValidationAlias, Query()],
):
    return {"p": p.p}