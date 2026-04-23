def read_required_validation_alias(
    p: Annotated[str, Body(embed=True, validation_alias="p_val_alias")],
):
    return {"p": p}