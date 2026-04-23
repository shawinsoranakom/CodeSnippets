def register_file_in_place(
    abs_path: str,
    name: str,
    tags: list[str],
    owner_id: str = "",
    mime_type: str | None = None,
) -> UploadResult:
    """Register an already-saved file in the asset database without moving it.

    Tags are derived from the filesystem path (root category + subfolder names),
    merged with any caller-provided tags, matching the behavior of the scanner.
    If the path is not under a known root, only the caller-provided tags are used.
    """
    try:
        _, path_tags = get_name_and_tags_from_asset_path(abs_path)
    except ValueError:
        path_tags = []
    merged_tags = normalize_tags([*path_tags, *tags])

    try:
        digest, _ = hashing.compute_blake3_hash(abs_path)
    except ImportError as e:
        raise DependencyMissingError(str(e))
    except Exception as e:
        raise RuntimeError(f"failed to hash file: {e}")
    asset_hash = "blake3:" + digest

    size_bytes, mtime_ns = get_size_and_mtime_ns(abs_path)
    content_type = mime_type or (
        mimetypes.guess_type(abs_path, strict=False)[0]
        or "application/octet-stream"
    )

    ingest_result = _ingest_file_from_path(
        abs_path=abs_path,
        asset_hash=asset_hash,
        size_bytes=size_bytes,
        mtime_ns=mtime_ns,
        mime_type=content_type,
        info_name=_sanitize_filename(name, fallback=digest),
        owner_id=owner_id,
        tags=merged_tags,
        tag_origin="upload",
        require_existing_tags=False,
    )
    reference_id = ingest_result.reference_id
    if not reference_id:
        raise RuntimeError("failed to create asset reference")

    with create_session() as session:
        pair = fetch_reference_and_asset(
            session, reference_id=reference_id, owner_id=owner_id
        )
        if not pair:
            raise RuntimeError("inconsistent DB state after ingest")
        ref, asset = pair
        tag_names = get_reference_tags(session, reference_id=ref.id)

    return UploadResult(
        ref=extract_reference_data(ref),
        asset=extract_asset_data(asset),
        tags=tag_names,
        created_new=ingest_result.asset_created,
    )