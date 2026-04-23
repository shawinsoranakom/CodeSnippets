async def read_optional_list_uploadfile_alias(
    p: Annotated[list[UploadFile] | None, File(alias="p_alias")] = None,
):
    return {"file_size": [file.size for file in p] if p else None}