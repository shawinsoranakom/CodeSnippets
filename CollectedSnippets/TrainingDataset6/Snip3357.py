async def read_optional_bytes(p: Annotated[bytes | None, File()] = None):
    return {"file_size": len(p) if p else None}