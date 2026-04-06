def read_required_bytes_validation_alias(
    p: Annotated[bytes, File(validation_alias="p_val_alias")],
):
    return {"file_size": len(p)}