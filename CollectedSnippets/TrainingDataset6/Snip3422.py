def read_required_bytes_alias_and_validation_alias(
    p: Annotated[bytes, File(alias="p_alias", validation_alias="p_val_alias")],
):
    return {"file_size": len(p)}