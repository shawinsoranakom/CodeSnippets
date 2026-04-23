def resolve_hash_to_path(
    asset_hash: str,
    owner_id: str = "",
) -> DownloadResolutionResult | None:
    """Resolve a blake3 hash to an on-disk file path.

    Only references visible to *owner_id* are considered (owner-less
    references are always visible).

    Returns a DownloadResolutionResult with abs_path, content_type, and
    download_name, or None if no asset or live path is found.
    """
    with create_session() as session:
        asset = queries_get_asset_by_hash(session, asset_hash)
        if not asset:
            return None
        refs = list_references_by_asset_id(session, asset_id=asset.id)
        visible = [
            r for r in refs
            if r.owner_id == "" or r.owner_id == owner_id
        ]
        abs_path = select_best_live_path(visible)
        if not abs_path:
            return None
        display_name = os.path.basename(abs_path)
        for ref in visible:
            if ref.file_path == abs_path and ref.name:
                display_name = ref.name
                break
        ctype = (
            asset.mime_type
            or mimetypes.guess_type(display_name)[0]
            or "application/octet-stream"
        )
    return DownloadResolutionResult(
        abs_path=abs_path,
        content_type=ctype,
        download_name=display_name,
    )