def read_model_optional_validation_alias(
    p: Annotated[HeaderModelOptionalValidationAlias, Header()],
):
    return {"p": p.p}