async def read_required_bytes(p: Annotated[bytes, File()]):
    return {"file_size": len(p)}