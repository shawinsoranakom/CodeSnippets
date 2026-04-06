def read_required_uploadfile_validation_alias(
    p: Annotated[UploadFile, File(validation_alias="p_val_alias")],
):
    return {"file_size": p.size}