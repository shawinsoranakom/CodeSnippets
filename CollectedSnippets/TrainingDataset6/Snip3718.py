def read_required_alias_and_validation_alias(
    p: Annotated[str, Query(alias="p_alias", validation_alias="p_val_alias")],
):
    return {"p": p}