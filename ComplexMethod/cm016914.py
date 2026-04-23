def extract_file_metadata(
    abs_path: str,
    stat_result: os.stat_result | None = None,
    relative_filename: str | None = None,
) -> ExtractedMetadata:
    """Extract metadata from a file using tier 1 and tier 2 methods.

    Tier 1: Filesystem metadata from path and stat
    Tier 2: Safetensors header parsing if applicable

    Args:
        abs_path: Absolute path to the file
        stat_result: Optional pre-fetched stat result (saves a syscall)
        relative_filename: Optional relative filename to use instead of basename
            (e.g., "flux/123/model.safetensors" for model paths)

    Returns:
        ExtractedMetadata with all available fields populated
    """
    meta = ExtractedMetadata()

    # Tier 1: Filesystem metadata
    meta.filename = relative_filename or os.path.basename(abs_path)
    meta.file_path = abs_path
    _, ext = os.path.splitext(abs_path)
    meta.format = ext.lstrip(".").lower() if ext else ""

    mime_type, _ = mimetypes.guess_type(abs_path)
    meta.content_type = mime_type

    # Size from stat
    if stat_result is None:
        try:
            stat_result = os.stat(abs_path, follow_symlinks=True)
        except OSError:
            pass

    if stat_result:
        meta.content_length = stat_result.st_size

    # Tier 2: Safetensors header (if applicable and enabled)
    if ext.lower() in SAFETENSORS_EXTENSIONS:
        header = _read_safetensors_header(abs_path)
        if header:
            try:
                _extract_safetensors_metadata(header, meta)
            except Exception as e:
                logging.debug("Safetensors meta extract failed %s: %s", abs_path, e)

    return meta