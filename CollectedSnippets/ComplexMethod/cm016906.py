def upload_from_temp_path(
    temp_path: str,
    name: str | None = None,
    tags: list[str] | None = None,
    user_metadata: dict | None = None,
    client_filename: str | None = None,
    owner_id: str = "",
    expected_hash: str | None = None,
    mime_type: str | None = None,
    preview_id: str | None = None,
) -> UploadResult:
    try:
        digest, _ = hashing.compute_blake3_hash(temp_path)
    except ImportError as e:
        raise DependencyMissingError(str(e))
    except Exception as e:
        raise RuntimeError(f"failed to hash uploaded file: {e}")
    asset_hash = "blake3:" + digest

    if expected_hash and asset_hash != expected_hash.strip().lower():
        raise HashMismatchError("Uploaded file hash does not match provided hash.")

    with create_session() as session:
        existing = get_asset_by_hash(session, asset_hash=asset_hash)

    if existing is not None:
        with contextlib.suppress(Exception):
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

        display_name = _sanitize_filename(name or client_filename, fallback=digest)
        result = _register_existing_asset(
            asset_hash=asset_hash,
            name=display_name,
            user_metadata=user_metadata or {},
            tags=tags or [],
            tag_origin="manual",
            owner_id=owner_id,
            mime_type=mime_type,
            preview_id=preview_id,
        )
        return UploadResult(
            ref=result.ref,
            asset=result.asset,
            tags=result.tags,
            created_new=False,
        )

    if not tags:
        raise ValueError("tags are required for new asset uploads")
    base_dir, subdirs = resolve_destination_from_tags(tags)
    dest_dir = os.path.join(base_dir, *subdirs) if subdirs else base_dir
    os.makedirs(dest_dir, exist_ok=True)

    src_for_ext = (client_filename or name or "").strip()
    _ext = os.path.splitext(os.path.basename(src_for_ext))[1] if src_for_ext else ""
    ext = _ext if 0 < len(_ext) <= 16 else ""
    hashed_basename = f"{digest}{ext}"
    dest_abs = os.path.abspath(os.path.join(dest_dir, hashed_basename))
    validate_path_within_base(dest_abs, base_dir)

    content_type = mime_type or (
        mimetypes.guess_type(os.path.basename(src_for_ext), strict=False)[0]
        or mimetypes.guess_type(hashed_basename, strict=False)[0]
        or "application/octet-stream"
    )

    try:
        os.replace(temp_path, dest_abs)
    except Exception as e:
        raise RuntimeError(f"failed to move uploaded file into place: {e}")

    try:
        size_bytes, mtime_ns = get_size_and_mtime_ns(dest_abs)
    except OSError as e:
        raise RuntimeError(f"failed to stat destination file: {e}")

    ingest_result = _ingest_file_from_path(
        asset_hash=asset_hash,
        abs_path=dest_abs,
        size_bytes=size_bytes,
        mtime_ns=mtime_ns,
        mime_type=content_type,
        info_name=_sanitize_filename(name or client_filename, fallback=digest),
        owner_id=owner_id,
        preview_id=preview_id,
        user_metadata=user_metadata or {},
        tags=tags,
        tag_origin="manual",
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