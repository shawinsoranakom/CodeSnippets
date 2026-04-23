def _extract_flows_sync(contents: bytes) -> _ZipExtractionResult:
    """Synchronous helper that performs all blocking ZIP I/O.

    Raises:
        ValueError: If the ZIP is corrupt or contains more than MAX_ZIP_ENTRIES JSON files.
    """
    result = _ZipExtractionResult()

    try:
        zf = zipfile.ZipFile(io.BytesIO(contents), "r")
    except zipfile.BadZipFile as exc:
        msg = f"Uploaded file is not a valid ZIP archive: {exc}"
        raise ValueError(msg) from exc

    with zf:
        json_entries = [info for info in zf.infolist() if info.filename.lower().endswith(".json")]

        if len(json_entries) > MAX_ZIP_ENTRIES:
            msg = f"ZIP contains {len(json_entries)} JSON entries, exceeding the limit of {MAX_ZIP_ENTRIES}"
            raise ValueError(msg)

        for info in json_entries:
            if info.file_size > MAX_ENTRY_UNCOMPRESSED_BYTES:
                result.warnings.append(
                    f"Skipping ZIP entry '{info.filename}': uncompressed size "
                    f"{info.file_size} exceeds limit of {MAX_ENTRY_UNCOMPRESSED_BYTES} bytes"
                )
                continue
            try:
                raw = zf.read(info.filename)
                if len(raw) > MAX_ENTRY_UNCOMPRESSED_BYTES:
                    result.warnings.append(
                        f"Skipping ZIP entry '{info.filename}': actual size "
                        f"{len(raw)} exceeds limit of {MAX_ENTRY_UNCOMPRESSED_BYTES} bytes"
                    )
                    continue
                result.flows.append(orjson.loads(raw))
            except orjson.JSONDecodeError:
                result.warnings.append(f"Skipping ZIP entry '{info.filename}': invalid JSON")
                continue

    return result