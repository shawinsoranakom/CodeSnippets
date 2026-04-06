def read_model_optional_list_validation_alias(
    p: Annotated[HeaderModelOptionalListValidationAlias, Header()],
):
    return {"p": p.p}