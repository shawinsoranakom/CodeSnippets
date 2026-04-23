def read_list_bytes_alias_and_validation_alias(
    p: Annotated[list[bytes], File(alias="p_alias", validation_alias="p_val_alias")],
):
    return {"file_size": [len(file) for file in p]}