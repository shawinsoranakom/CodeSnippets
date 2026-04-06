def read_model_required_alias_and_validation_alias(
    p: Annotated[CookieModelRequiredAliasAndValidationAlias, Cookie()],
):
    return {"p": p.p}