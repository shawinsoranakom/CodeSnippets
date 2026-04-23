def read_list_uploadfile_alias_and_validation_alias(
    p: Annotated[
        list[UploadFile], File(alias="p_alias", validation_alias="p_val_alias")
    ],
):
    return {"file_size": [file.size for file in p]}