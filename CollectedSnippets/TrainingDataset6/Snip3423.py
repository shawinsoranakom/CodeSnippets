def read_required_uploadfile_alias_and_validation_alias(
    p: Annotated[UploadFile, File(alias="p_alias", validation_alias="p_val_alias")],
):
    return {"file_size": p.size}