async def upload_files(files: list[bytes] | None = File(None)):
    if files is None:
        return {"files_count": 0}
    return {"files_count": len(files), "sizes": [len(f) for f in files]}