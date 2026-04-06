async def read_optional_list_bytes(p: Annotated[list[bytes] | None, File()] = None):
    return {"file_size": [len(file) for file in p] if p else None}