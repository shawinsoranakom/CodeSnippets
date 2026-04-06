def read_model_required_validation_alias(
    p: Annotated[CookieModelRequiredValidationAlias, Cookie()],
):
    return {"p": p.p}