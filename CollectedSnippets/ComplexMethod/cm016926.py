def list_tags_with_usage(
    session: Session,
    prefix: str | None = None,
    limit: int = 100,
    offset: int = 0,
    include_zero: bool = True,
    order: str = "count_desc",
    owner_id: str = "",
) -> tuple[list[tuple[str, str, int]], int]:
    counts_sq = (
        select(
            AssetReferenceTag.tag_name.label("tag_name"),
            func.count(AssetReferenceTag.asset_reference_id).label("cnt"),
        )
        .select_from(AssetReferenceTag)
        .join(AssetReference, AssetReference.id == AssetReferenceTag.asset_reference_id)
        .where(build_visible_owner_clause(owner_id))
        .where(
            sa.or_(
                AssetReference.is_missing == False,  # noqa: E712
                AssetReferenceTag.tag_name == "missing",
            )
        )
        .where(AssetReference.deleted_at.is_(None))
        .group_by(AssetReferenceTag.tag_name)
        .subquery()
    )

    q = (
        select(
            Tag.name,
            Tag.tag_type,
            func.coalesce(counts_sq.c.cnt, 0).label("count"),
        )
        .select_from(Tag)
        .join(counts_sq, counts_sq.c.tag_name == Tag.name, isouter=True)
    )

    if prefix:
        escaped, esc = escape_sql_like_string(prefix.strip().lower())
        q = q.where(Tag.name.like(escaped + "%", escape=esc))

    if not include_zero:
        q = q.where(func.coalesce(counts_sq.c.cnt, 0) > 0)

    if order == "name_asc":
        q = q.order_by(Tag.name.asc())
    else:
        q = q.order_by(func.coalesce(counts_sq.c.cnt, 0).desc(), Tag.name.asc())

    total_q = select(func.count()).select_from(Tag)
    if prefix:
        escaped, esc = escape_sql_like_string(prefix.strip().lower())
        total_q = total_q.where(Tag.name.like(escaped + "%", escape=esc))
    if not include_zero:
        visible_tags_sq = (
            select(AssetReferenceTag.tag_name)
            .join(AssetReference, AssetReference.id == AssetReferenceTag.asset_reference_id)
            .where(build_visible_owner_clause(owner_id))
            .where(
                sa.or_(
                    AssetReference.is_missing == False,  # noqa: E712
                    AssetReferenceTag.tag_name == "missing",
                )
            )
            .where(AssetReference.deleted_at.is_(None))
            .group_by(AssetReferenceTag.tag_name)
        )
        total_q = total_q.where(Tag.name.in_(visible_tags_sq))

    rows = (session.execute(q.limit(limit).offset(offset))).all()
    total = (session.execute(total_q)).scalar_one()

    rows_norm = [(name, ttype, int(count or 0)) for (name, ttype, count) in rows]
    return rows_norm, int(total or 0)