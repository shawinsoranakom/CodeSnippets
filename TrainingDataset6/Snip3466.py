def read_model_optional_list_validation_alias(
    p: Annotated[FormModelOptionalListValidationAlias, Form()],
):
    return {"p": p.p}