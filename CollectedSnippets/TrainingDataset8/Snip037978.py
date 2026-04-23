def _calculate_file_id(
    data: bytes, mimetype: str, filename: Optional[str] = None
) -> str:
    """Hash data, mimetype, and an optional filename to generate a stable file ID.

    Parameters
    ----------
    data
        Content of in-memory file in bytes. Other types will throw TypeError.
    mimetype
        Any string. Will be converted to bytes and used to compute a hash.
    filename
        Any string. Will be converted to bytes and used to compute a hash.
    """
    filehash = hashlib.new("sha224")
    filehash.update(data)
    filehash.update(bytes(mimetype.encode()))

    if filename is not None:
        filehash.update(bytes(filename.encode()))

    return filehash.hexdigest()