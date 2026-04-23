def list_references_page(
    session: Session,
    owner_id: str = "",
    limit: int = 100,
    offset: int = 0,
    name_contains: str | None = None,
    include_tags: Sequence[str] | None = None,
    exclude_tags: Sequence[str] | None = None,
    metadata_filter: dict | None = None,
    sort: str | None = None,
    order: str | None = None,
) -> tuple[list[AssetReference], dict[str, list[str]], int]:
    """List references with pagination, filtering, and sorting.

    Returns (references, tag_map, total_count).
    """
    base = (
        select(AssetReference)
        .join(Asset, Asset.id == AssetReference.asset_id)
        .where(build_visible_owner_clause(owner_id))
        .where(AssetReference.is_missing == False)  # noqa: E712
        .where(AssetReference.deleted_at.is_(None))
        .options(noload(AssetReference.tags))
    )

    if name_contains:
        escaped, esc = escape_sql_like_string(name_contains)
        base = base.where(AssetReference.name.ilike(f"%{escaped}%", escape=esc))

    base = apply_tag_filters(base, include_tags, exclude_tags)
    base = apply_metadata_filter(base, metadata_filter)

    sort = (sort or "created_at").lower()
    order = (order or "desc").lower()
    sort_map = {
        "name": AssetReference.name,
        "created_at": AssetReference.created_at,
        "updated_at": AssetReference.updated_at,
        "last_access_time": AssetReference.last_access_time,
        "size": Asset.size_bytes,
    }
    sort_col = sort_map.get(sort, AssetReference.created_at)
    sort_exp = sort_col.desc() if order == "desc" else sort_col.asc()

    base = base.order_by(sort_exp).limit(limit).offset(offset)

    count_stmt = (
        select(sa.func.count())
        .select_from(AssetReference)
        .join(Asset, Asset.id == AssetReference.asset_id)
        .where(build_visible_owner_clause(owner_id))
        .where(AssetReference.is_missing == False)  # noqa: E712
        .where(AssetReference.deleted_at.is_(None))
    )
    if name_contains:
        escaped, esc = escape_sql_like_string(name_contains)
        count_stmt = count_stmt.where(
            AssetReference.name.ilike(f"%{escaped}%", escape=esc)
        )
    count_stmt = apply_tag_filters(count_stmt, include_tags, exclude_tags)
    count_stmt = apply_metadata_filter(count_stmt, metadata_filter)

    total = int(session.execute(count_stmt).scalar_one() or 0)
    refs = session.execute(base).unique().scalars().all()

    id_list: list[str] = [r.id for r in refs]
    tag_map: dict[str, list[str]] = defaultdict(list)
    if id_list:
        rows = session.execute(
            select(AssetReferenceTag.asset_reference_id, Tag.name)
            .join(Tag, Tag.name == AssetReferenceTag.tag_name)
            .where(AssetReferenceTag.asset_reference_id.in_(id_list))
            .order_by(AssetReferenceTag.tag_name.asc())
        )
        for ref_id, tag_name in rows.all():
            tag_map[ref_id].append(tag_name)

    return list(refs), tag_map, total