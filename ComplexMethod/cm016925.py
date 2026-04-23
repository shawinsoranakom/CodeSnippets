def remove_tags_from_reference(
    session: Session,
    reference_id: str,
    tags: Sequence[str],
) -> RemoveTagsResult:
    ref = session.get(AssetReference, reference_id)
    if not ref:
        raise ValueError(f"AssetReference {reference_id} not found")

    norm = normalize_tags(tags)
    if not norm:
        total = get_reference_tags(session, reference_id=reference_id)
        return RemoveTagsResult(removed=[], not_present=[], total_tags=total)

    existing = set(get_reference_tags(session, reference_id))

    to_remove = sorted(set(t for t in norm if t in existing))
    not_present = sorted(set(t for t in norm if t not in existing))

    if to_remove:
        session.execute(
            delete(AssetReferenceTag).where(
                AssetReferenceTag.asset_reference_id == reference_id,
                AssetReferenceTag.tag_name.in_(to_remove),
            )
        )
        session.flush()

    total = get_reference_tags(session, reference_id=reference_id)
    return RemoveTagsResult(removed=to_remove, not_present=not_present, total_tags=total)