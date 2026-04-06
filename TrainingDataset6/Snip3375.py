def read_optional_uploadfile_alias_and_validation_alias(
    p: Annotated[
        UploadFile | None, File(alias="p_alias", validation_alias="p_val_alias")
    ] = None,
):
    return {"file_size": p.size if p else None}