def read_optional_alias_and_validation_alias(
    p: Annotated[
        str | None, Cookie(alias="p_alias", validation_alias="p_val_alias")
    ] = None,
):
    return {"p": p}