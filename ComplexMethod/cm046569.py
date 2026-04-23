def _build_local_dataset_items() -> list[LocalDatasetItem]:
    if not LOCAL_DATASETS_ROOT.exists():
        return []

    items: list[LocalDatasetItem] = []
    for entry in LOCAL_DATASETS_ROOT.iterdir():
        if not entry.is_dir() or not entry.name.startswith("recipe_"):
            continue
        parquet_dir = entry / "parquet-files"
        if not parquet_dir.exists() or not any(parquet_dir.glob("*.parquet")):
            continue

        rows = None
        metadata_summary = None
        metadata_path = entry / "metadata.json"
        if metadata_path.exists():
            metadata_payload = _safe_read_metadata(metadata_path)
            rows = _safe_read_rows_from_metadata(metadata_payload)
            metadata_summary = _safe_read_metadata_summary(metadata_payload)

        try:
            updated_at = entry.stat().st_mtime
        except OSError:
            updated_at = None

        items.append(
            LocalDatasetItem(
                id = entry.name,
                label = entry.name,
                path = str(parquet_dir.resolve()),
                rows = rows,
                updated_at = updated_at,
                metadata = metadata_summary,
            )
        )

    items.sort(key = lambda item: item.updated_at or 0, reverse = True)
    return items