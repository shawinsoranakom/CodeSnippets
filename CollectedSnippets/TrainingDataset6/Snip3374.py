def read_optional_bytes_alias_and_validation_alias(
    p: Annotated[
        bytes | None, File(alias="p_alias", validation_alias="p_val_alias")
    ] = None,
):
    return {"file_size": len(p) if p else None}