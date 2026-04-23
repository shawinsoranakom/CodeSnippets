def _ingest_file_from_path(
    abs_path: str,
    asset_hash: str,
    size_bytes: int,
    mtime_ns: int,
    mime_type: str | None = None,
    info_name: str | None = None,
    owner_id: str = "",
    preview_id: str | None = None,
    user_metadata: UserMetadata = None,
    tags: Sequence[str] = (),
    tag_origin: str = "manual",
    require_existing_tags: bool = False,
) -> IngestResult:
    locator = os.path.abspath(abs_path)
    user_metadata = user_metadata or {}

    asset_created = False
    asset_updated = False
    ref_created = False
    ref_updated = False
    reference_id: str | None = None

    with create_session() as session:
        if preview_id:
            if not reference_exists(session, preview_id):
                preview_id = None

        asset, asset_created, asset_updated = upsert_asset(
            session,
            asset_hash=asset_hash,
            size_bytes=size_bytes,
            mime_type=mime_type,
        )

        ref_created, ref_updated = upsert_reference(
            session,
            asset_id=asset.id,
            file_path=locator,
            name=info_name or os.path.basename(locator),
            mtime_ns=mtime_ns,
            owner_id=owner_id,
        )

        # Get the reference we just created/updated
        ref = get_reference_by_file_path(session, locator)
        if ref:
            reference_id = ref.id

            if preview_id and ref.preview_id != preview_id:
                ref.preview_id = preview_id

            norm = normalize_tags(list(tags))
            if norm:
                if require_existing_tags:
                    validate_tags_exist(session, norm)
                add_tags_to_reference(
                    session,
                    reference_id=reference_id,
                    tags=norm,
                    origin=tag_origin,
                    create_if_missing=not require_existing_tags,
                )

            _update_metadata_with_filename(
                session,
                reference_id=reference_id,
                file_path=ref.file_path,
                current_metadata=ref.user_metadata,
                user_metadata=user_metadata,
            )

        try:
            remove_missing_tag_for_asset_id(session, asset_id=asset.id)
        except Exception:
            logging.exception("Failed to clear 'missing' tag for asset %s", asset.id)

        session.commit()

    return IngestResult(
        asset_created=asset_created,
        asset_updated=asset_updated,
        ref_created=ref_created,
        ref_updated=ref_updated,
        reference_id=reference_id,
    )