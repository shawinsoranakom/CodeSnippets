def set_reference_tags(
    session: Session,
    reference_id: str,
    tags: Sequence[str],
    origin: str = "manual",
) -> SetTagsResult:
    desired = normalize_tags(tags)

    current = set(get_reference_tags(session, reference_id))

    to_add = [t for t in desired if t not in current]
    to_remove = [t for t in current if t not in desired]

    if to_add:
        ensure_tags_exist(session, to_add, tag_type="user")
        session.add_all(
            [
                AssetReferenceTag(
                    asset_reference_id=reference_id,
                    tag_name=t,
                    origin=origin,
                    added_at=get_utc_now(),
                )
                for t in to_add
            ]
        )
        session.flush()

    if to_remove:
        session.execute(
            delete(AssetReferenceTag).where(
                AssetReferenceTag.asset_reference_id == reference_id,
                AssetReferenceTag.tag_name.in_(to_remove),
            )
        )
        session.flush()

    return SetTagsResult(added=sorted(to_add), removed=sorted(to_remove), total=sorted(desired))