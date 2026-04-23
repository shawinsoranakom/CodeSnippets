def upsert_asset(
    session: Session,
    asset_hash: str,
    size_bytes: int,
    mime_type: str | None = None,
) -> tuple[Asset, bool, bool]:
    """Upsert an Asset by hash. Returns (asset, created, updated)."""
    vals = {"hash": asset_hash, "size_bytes": int(size_bytes)}
    if mime_type:
        vals["mime_type"] = mime_type

    ins = (
        sqlite.insert(Asset)
        .values(**vals)
        .on_conflict_do_nothing(index_elements=[Asset.hash])
    )
    res = session.execute(ins)
    created = int(res.rowcount or 0) > 0

    asset = (
        session.execute(select(Asset).where(Asset.hash == asset_hash).limit(1))
        .scalars()
        .first()
    )
    if not asset:
        raise RuntimeError("Asset row not found after upsert.")

    updated = False
    if not created:
        changed = False
        if asset.size_bytes != int(size_bytes) and int(size_bytes) > 0:
            asset.size_bytes = int(size_bytes)
            changed = True
        if mime_type and not asset.mime_type:
            asset.mime_type = mime_type
            changed = True
        if changed:
            updated = True

    return asset, created, updated