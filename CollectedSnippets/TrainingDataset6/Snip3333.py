async def read_list_bytes(p: Annotated[list[bytes], File()]):
    return {"file_size": [len(file) for file in p]}