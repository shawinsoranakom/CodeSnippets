def read_model_required_list_alias_and_validation_alias(
    p: Annotated[HeaderModelRequiredListAliasAndValidationAlias, Header()],
):
    return {"p": p.p}