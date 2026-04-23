async def read_optional_list_bytes_alias(
    p: Annotated[list[bytes] | None, File(alias="p_alias")] = None,
):
    return {"file_size": [len(file) for file in p] if p else None}