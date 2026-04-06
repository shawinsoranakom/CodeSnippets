async def read_optional_uploadfile(p: Annotated[UploadFile | None, File()] = None):
    return {"file_size": p.size if p else None}