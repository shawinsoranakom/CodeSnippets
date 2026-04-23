async def read_optional_bytes_alias(
    p: Annotated[bytes | None, File(alias="p_alias")] = None,
):
    return {"file_size": len(p) if p else None}