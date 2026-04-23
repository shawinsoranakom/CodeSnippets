async def read_required_uploadfile_alias(
    p: Annotated[UploadFile, File(alias="p_alias")],
):
    return {"file_size": p.size}