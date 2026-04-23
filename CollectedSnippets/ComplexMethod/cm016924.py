def add_tags_to_reference(
    session: Session,
    reference_id: str,
    tags: Sequence[str],
    origin: str = "manual",
    create_if_missing: bool = True,
    reference_row: AssetReference | None = None,
) -> AddTagsResult:
    if not reference_row:
        ref = session.get(AssetReference, reference_id)
        if not ref:
            raise ValueError(f"AssetReference {reference_id} not found")

    norm = normalize_tags(tags)
    if not norm:
        total = get_reference_tags(session, reference_id=reference_id)
        return AddTagsResult(added=[], already_present=[], total_tags=total)

    if create_if_missing:
        ensure_tags_exist(session, norm, tag_type="user")

    current = set(get_reference_tags(session, reference_id))

    want = set(norm)
    to_add = sorted(want - current)

    if to_add:
        with session.begin_nested() as nested:
            try:
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
            except IntegrityError:
                nested.rollback()

    after = set(get_reference_tags(session, reference_id=reference_id))
    return AddTagsResult(
        added=sorted(((after - current) & want)),
        already_present=sorted(want & current),
        total_tags=sorted(after),
    )