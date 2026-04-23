async def read_list_uploadfile_alias(
    p: Annotated[list[UploadFile], File(alias="p_alias")],
):
    return {"file_size": [file.size for file in p]}