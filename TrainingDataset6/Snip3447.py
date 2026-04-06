def read_required_list_alias_and_validation_alias(
    p: Annotated[list[str], Form(alias="p_alias", validation_alias="p_val_alias")],
):
    return {"p": p}