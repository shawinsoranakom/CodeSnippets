def read_optional_uploadfile_validation_alias(
    p: Annotated[UploadFile | None, File(validation_alias="p_val_alias")] = None,
):
    return {"file_size": p.size if p else None}