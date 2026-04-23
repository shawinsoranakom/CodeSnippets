def _register_existing_asset(
    asset_hash: str,
    name: str,
    user_metadata: UserMetadata = None,
    tags: list[str] | None = None,
    tag_origin: str = "manual",
    owner_id: str = "",
    mime_type: str | None = None,
    preview_id: str | None = None,
) -> RegisterAssetResult:
    user_metadata = user_metadata or {}

    with create_session() as session:
        asset = get_asset_by_hash(session, asset_hash=asset_hash)
        if not asset:
            raise ValueError(f"No asset with hash {asset_hash}")

        if mime_type and not asset.mime_type:
            update_asset_hash_and_mime(session, asset_id=asset.id, mime_type=mime_type)

        if preview_id:
            if not reference_exists(session, preview_id):
                preview_id = None

        ref, ref_created = get_or_create_reference(
            session,
            asset_id=asset.id,
            owner_id=owner_id,
            name=name,
            preview_id=preview_id,
        )

        if not ref_created:
            if preview_id and ref.preview_id != preview_id:
                ref.preview_id = preview_id

            tag_names = get_reference_tags(session, reference_id=ref.id)
            result = RegisterAssetResult(
                ref=extract_reference_data(ref),
                asset=extract_asset_data(asset),
                tags=tag_names,
                created=False,
            )
            session.commit()
            return result

        new_meta = dict(user_metadata)
        computed_filename = compute_relative_filename(ref.file_path) if ref.file_path else None
        if computed_filename:
            new_meta["filename"] = computed_filename

        if new_meta:
            set_reference_metadata(
                session,
                reference_id=ref.id,
                user_metadata=new_meta,
            )

        if tags is not None:
            set_reference_tags(
                session,
                reference_id=ref.id,
                tags=tags,
                origin=tag_origin,
            )

        tag_names = get_reference_tags(session, reference_id=ref.id)
        session.refresh(ref)
        result = RegisterAssetResult(
            ref=extract_reference_data(ref),
            asset=extract_asset_data(asset),
            tags=tag_names,
            created=True,
        )
        session.commit()

        return result