def read_optional_list_bytes_validation_alias(
    p: Annotated[list[bytes] | None, File(validation_alias="p_val_alias")] = None,
):
    return {"file_size": [len(file) for file in p] if p else None}