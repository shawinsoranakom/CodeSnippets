async def read_required_uploadfile(p: Annotated[UploadFile, File()]):
    return {"file_size": p.size}