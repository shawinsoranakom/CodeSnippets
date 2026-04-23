def read_required_alias_and_validation_alias(
    p: Annotated[str, Header(alias="p_alias", validation_alias="p_val_alias")],
):
    return {"p": p}