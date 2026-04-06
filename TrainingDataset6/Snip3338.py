async def read_list_bytes_alias(p: Annotated[list[bytes], File(alias="p_alias")]):
    return {"file_size": [len(file) for file in p]}