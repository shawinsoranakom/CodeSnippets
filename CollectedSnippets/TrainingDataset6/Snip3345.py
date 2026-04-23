def read_list_uploadfile_validation_alias(
    p: Annotated[list[UploadFile], File(validation_alias="p_val_alias")],
):
    return {"file_size": [file.size for file in p]}