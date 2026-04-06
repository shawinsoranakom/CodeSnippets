def read_required_list_validation_alias(
    p: Annotated[list[str], Query(validation_alias="p_val_alias")],
):
    return {"p": p}