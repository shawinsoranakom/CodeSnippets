def read_list_bytes_validation_alias(
    p: Annotated[list[bytes], File(validation_alias="p_val_alias")],
):
    return {"file_size": [len(file) for file in p]}