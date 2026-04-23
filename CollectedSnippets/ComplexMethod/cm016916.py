def update_asset_metadata(
    reference_id: str,
    name: str | None = None,
    tags: Sequence[str] | None = None,
    user_metadata: UserMetadata = None,
    tag_origin: str = "manual",
    owner_id: str = "",
    mime_type: str | None = None,
    preview_id: str | None = None,
) -> AssetDetailResult:
    with create_session() as session:
        ref = get_reference_with_owner_check(session, reference_id, owner_id)

        touched = False
        if name is not None and name != ref.name:
            update_reference_name(session, reference_id=reference_id, name=name)
            touched = True

        computed_filename = compute_relative_filename(ref.file_path) if ref.file_path else None

        new_meta: dict | None = None
        if user_metadata is not None:
            new_meta = dict(user_metadata)
        elif computed_filename:
            current_meta = ref.user_metadata or {}
            if current_meta.get("filename") != computed_filename:
                new_meta = dict(current_meta)

        if new_meta is not None:
            if computed_filename:
                new_meta["filename"] = computed_filename
            set_reference_metadata(
                session, reference_id=reference_id, user_metadata=new_meta
            )
            touched = True

        if tags is not None:
            set_reference_tags(
                session,
                reference_id=reference_id,
                tags=tags,
                origin=tag_origin,
            )
            touched = True

        if mime_type is not None:
            updated = update_asset_hash_and_mime(
                session, asset_id=ref.asset_id, mime_type=mime_type
            )
            if updated:
                touched = True

        if preview_id is not None:
            set_reference_preview(
                session,
                reference_id=reference_id,
                preview_reference_id=preview_id,
            )
            touched = True

        if touched and user_metadata is None:
            update_reference_updated_at(session, reference_id=reference_id)

        result = fetch_reference_asset_and_tags(
            session,
            reference_id=reference_id,
            owner_id=owner_id,
        )
        if not result:
            raise RuntimeError("State changed during update")

        ref, asset, tag_list = result
        detail = AssetDetailResult(
            ref=extract_reference_data(ref),
            asset=extract_asset_data(asset),
            tags=tag_list,
        )
        session.commit()

        return detail