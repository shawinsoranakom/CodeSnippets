def get_extension_for_mimetype(mimetype: str) -> str:
    if mimetype in PREFERRED_MIMETYPE_EXTENSION_MAP:
        return PREFERRED_MIMETYPE_EXTENSION_MAP[mimetype]

    extension = mimetypes.guess_extension(mimetype, strict=False)
    if extension is None:
        return ""

    return extension