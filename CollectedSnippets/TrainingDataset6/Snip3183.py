def read_required_list_validation_alias(
    p: Annotated[list[str], Body(embed=True, validation_alias="p_val_alias")],
):
    return {"p": p}