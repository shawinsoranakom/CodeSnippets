def read_model_optional_validation_alias(
    p: Annotated[CookieModelOptionalValidationAlias, Cookie()],
):
    return {"p": p.p}