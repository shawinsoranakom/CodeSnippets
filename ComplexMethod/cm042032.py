async def get_mime_type(filename: str | Path, force_read: bool = False) -> str:
    guess_mime_type, _ = mimetypes.guess_type(filename.name)
    if not guess_mime_type:
        ext_mappings = {".yml": "text/yaml", ".yaml": "text/yaml"}
        guess_mime_type = ext_mappings.get(filename.suffix)
    if not force_read and guess_mime_type:
        return guess_mime_type

    from metagpt.tools.libs.shell import shell_execute  # avoid circular import

    text_set = {
        "application/json",
        "application/vnd.chipnuts.karaoke-mmd",
        "application/javascript",
        "application/xml",
        "application/x-sh",
        "application/sql",
        "text/yaml",
    }

    try:
        stdout, stderr, _ = await shell_execute(f"file --mime-type '{str(filename)}'")
        if stderr:
            logger.debug(f"file:{filename}, error:{stderr}")
            return guess_mime_type
        ix = stdout.rfind(" ")
        mime_type = stdout[ix:].strip()
        if mime_type == "text/plain" and guess_mime_type in text_set:
            return guess_mime_type
        return mime_type
    except Exception as e:
        logger.debug(f"file:{filename}, error:{e}")
        return "unknown"