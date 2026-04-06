def read_model_optional_validation_alias(
    p: Annotated[QueryModelOptionalValidationAlias, Query()],
):
    return {"p": p.p}