def read_required_validation_alias(
    p: Annotated[str, Form(validation_alias="p_val_alias")],
):
    return {"p": p}