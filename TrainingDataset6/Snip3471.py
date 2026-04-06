def read_optional_list_alias_and_validation_alias(
    p: Annotated[
        list[str] | None, Form(alias="p_alias", validation_alias="p_val_alias")
    ] = None,
):
    return {"p": p}