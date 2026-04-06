async def read_required_bytes_alias(p: Annotated[bytes, File(alias="p_alias")]):
    return {"file_size": len(p)}