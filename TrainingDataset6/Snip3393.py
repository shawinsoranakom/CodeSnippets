def read_optional_list_uploadfile_validation_alias(
    p: Annotated[list[UploadFile] | None, File(validation_alias="p_val_alias")] = None,
):
    return {"file_size": [file.size for file in p] if p else None}