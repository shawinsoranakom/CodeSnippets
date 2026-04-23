def resolve_asset_for_download(
    reference_id: str,
    owner_id: str = "",
) -> DownloadResolutionResult:
    with create_session() as session:
        pair = fetch_reference_and_asset(
            session, reference_id=reference_id, owner_id=owner_id
        )
        if not pair:
            raise ValueError(f"AssetReference {reference_id} not found")

        ref, asset = pair

        # For references with file_path, use that directly
        if ref.file_path and os.path.isfile(ref.file_path):
            abs_path = ref.file_path
        else:
            # For API-created refs without file_path, find a path from other refs
            refs = list_references_by_asset_id(session, asset_id=asset.id)
            abs_path = select_best_live_path(refs)
            if not abs_path:
                raise FileNotFoundError(
                    f"No live path for AssetReference {reference_id} "
                    f"(asset id={asset.id}, name={ref.name})"
                )

        # Capture ORM attributes before commit (commit expires loaded objects)
        ref_name = ref.name
        asset_mime = asset.mime_type

        update_reference_access_time(session, reference_id=reference_id)
        session.commit()

        ctype = (
            asset_mime
            or mimetypes.guess_type(ref_name or abs_path)[0]
            or "application/octet-stream"
        )
        download_name = ref_name or os.path.basename(abs_path)
        return DownloadResolutionResult(
            abs_path=abs_path,
            content_type=ctype,
            download_name=download_name,
        )