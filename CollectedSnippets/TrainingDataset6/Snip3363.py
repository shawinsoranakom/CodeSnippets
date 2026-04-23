async def read_optional_uploadfile_alias(
    p: Annotated[UploadFile | None, File(alias="p_alias")] = None,
):
    return {"file_size": p.size if p else None}