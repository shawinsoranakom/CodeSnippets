async def read_optional_list_uploadfile(
    p: Annotated[list[UploadFile] | None, File()] = None,
):
    return {"file_size": [file.size for file in p] if p else None}