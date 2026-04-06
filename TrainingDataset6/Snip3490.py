def read_model_optional_validation_alias(
    p: Annotated[FormModelOptionalValidationAlias, Form()],
):
    return {"p": p.p}