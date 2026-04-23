def read_optional_validation_alias(
    p: Annotated[str | None, Cookie(validation_alias="p_val_alias")] = None,
):
    return {"p": p}