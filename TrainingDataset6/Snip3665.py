def read_model_optional_list_validation_alias(
    p: Annotated[QueryModelOptionalListValidationAlias, Query()],
):
    return {"p": p.p}