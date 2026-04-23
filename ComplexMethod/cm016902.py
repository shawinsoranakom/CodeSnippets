def build_asset_specs(
    paths: list[str],
    existing_paths: set[str],
    enable_metadata_extraction: bool = True,
    compute_hashes: bool = False,
) -> tuple[list[SeedAssetSpec], set[str], int]:
    """Build asset specs from paths, returning (specs, tag_pool, skipped_count).

    Args:
        paths: List of file paths to process
        existing_paths: Set of paths that already exist in the database
        enable_metadata_extraction: If True, extract tier 1 & 2 metadata
        compute_hashes: If True, compute blake3 hashes (slow for large files)
    """
    specs: list[SeedAssetSpec] = []
    tag_pool: set[str] = set()
    skipped = 0

    for p in paths:
        abs_p = os.path.abspath(p)
        if abs_p in existing_paths:
            skipped += 1
            continue
        try:
            stat_p = os.stat(abs_p, follow_symlinks=True)
        except OSError:
            continue
        if not stat_p.st_size:
            continue
        name, tags = get_name_and_tags_from_asset_path(abs_p)
        rel_fname = compute_relative_filename(abs_p)

        # Extract metadata (tier 1: filesystem, tier 2: safetensors header)
        metadata = None
        if enable_metadata_extraction:
            metadata = extract_file_metadata(
                abs_p,
                stat_result=stat_p,
                relative_filename=rel_fname,
            )

        # Compute hash if requested
        asset_hash: str | None = None
        if compute_hashes:
            try:
                digest, _ = compute_blake3_hash(abs_p)
                asset_hash = "blake3:" + digest
            except Exception as e:
                logging.warning("Failed to hash %s: %s", abs_p, e)

        mime_type = metadata.content_type if metadata else None
        specs.append(
            {
                "abs_path": abs_p,
                "size_bytes": stat_p.st_size,
                "mtime_ns": get_mtime_ns(stat_p),
                "info_name": name,
                "tags": tags,
                "fname": rel_fname,
                "metadata": metadata,
                "hash": asset_hash,
                "mime_type": mime_type,
                "job_id": None,
            }
        )
        tag_pool.update(tags)

    return specs, tag_pool, skipped