def read_optional_list_validation_alias(
    p: Annotated[
        list[str] | None, Body(embed=True, validation_alias="p_val_alias")
    ] = None,
):
    return {"p": p}