async def read_list_uploadfile(p: Annotated[list[UploadFile], File()]):
    return {"file_size": [file.size for file in p]}