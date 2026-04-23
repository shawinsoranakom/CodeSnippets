def enrich_asset(
    session,
    file_path: str,
    reference_id: str,
    asset_id: str,
    extract_metadata: bool = True,
    compute_hash: bool = False,
    interrupt_check: Callable[[], bool] | None = None,
    hash_checkpoints: dict[str, HashCheckpoint] | None = None,
) -> int:
    """Enrich a single asset with metadata and/or hash.

    Args:
        session: Database session (caller manages lifecycle)
        file_path: Absolute path to the file
        reference_id: ID of the reference to update
        asset_id: ID of the asset to update (for mime_type and hash)
        extract_metadata: If True, extract safetensors header and mime type
        compute_hash: If True, compute blake3 hash
        interrupt_check: Optional non-blocking callable that returns True if
            the operation should be interrupted (e.g. paused or cancelled)
        hash_checkpoints: Optional dict for saving/restoring hash progress
            across interruptions, keyed by file path

    Returns:
        New enrichment level achieved
    """
    new_level = ENRICHMENT_STUB

    try:
        stat_p = os.stat(file_path, follow_symlinks=True)
    except OSError:
        return new_level

    initial_mtime_ns = get_mtime_ns(stat_p)
    rel_fname = compute_relative_filename(file_path)
    mime_type: str | None = None
    metadata = None

    if extract_metadata:
        metadata = extract_file_metadata(
            file_path,
            stat_result=stat_p,
            relative_filename=rel_fname,
        )
        if metadata:
            mime_type = metadata.content_type
            new_level = ENRICHMENT_METADATA

    full_hash: str | None = None
    if compute_hash:
        try:
            mtime_before = get_mtime_ns(stat_p)
            size_before = stat_p.st_size

            # Restore checkpoint if available and file unchanged
            checkpoint = None
            if hash_checkpoints is not None:
                checkpoint = hash_checkpoints.get(file_path)
                if checkpoint is not None:
                    cur_stat = os.stat(file_path, follow_symlinks=True)
                    if (checkpoint.mtime_ns != get_mtime_ns(cur_stat)
                            or checkpoint.file_size != cur_stat.st_size):
                        checkpoint = None
                        hash_checkpoints.pop(file_path, None)
                    else:
                        mtime_before = get_mtime_ns(cur_stat)

            digest, new_checkpoint = compute_blake3_hash(
                file_path,
                interrupt_check=interrupt_check,
                checkpoint=checkpoint,
            )

            if digest is None:
                # Interrupted — save checkpoint for later resumption
                if hash_checkpoints is not None and new_checkpoint is not None:
                    new_checkpoint.mtime_ns = mtime_before
                    new_checkpoint.file_size = size_before
                    hash_checkpoints[file_path] = new_checkpoint
                return new_level

            # Completed — clear any saved checkpoint
            if hash_checkpoints is not None:
                hash_checkpoints.pop(file_path, None)

            stat_after = os.stat(file_path, follow_symlinks=True)
            mtime_after = get_mtime_ns(stat_after)
            if mtime_before != mtime_after:
                logging.warning("File modified during hashing, discarding hash: %s", file_path)
            else:
                full_hash = f"blake3:{digest}"
                metadata_ok = not extract_metadata or metadata is not None
                if metadata_ok:
                    new_level = ENRICHMENT_HASHED
        except Exception as e:
            logging.warning("Failed to hash %s: %s", file_path, e)

    # Optimistic guard: if the reference's mtime_ns changed since we
    # started (e.g. ingest_existing_file updated it), our results are
    # stale — discard them to avoid overwriting fresh registration data.
    ref = get_reference_by_id(session, reference_id)
    if ref is None or ref.mtime_ns != initial_mtime_ns:
        session.rollback()
        logging.info(
            "Ref %s mtime changed during enrichment, discarding stale result",
            reference_id,
        )
        return ENRICHMENT_STUB

    if extract_metadata and metadata:
        system_metadata = metadata.to_user_metadata()
        set_reference_system_metadata(session, reference_id, system_metadata)

    if full_hash:
        existing = get_asset_by_hash(session, full_hash)
        if existing and existing.id != asset_id:
            reassign_asset_references(session, asset_id, existing.id, reference_id)
            delete_orphaned_seed_asset(session, asset_id)
            if mime_type:
                update_asset_hash_and_mime(session, existing.id, mime_type=mime_type)
        else:
            update_asset_hash_and_mime(session, asset_id, full_hash, mime_type)
    elif mime_type:
        update_asset_hash_and_mime(session, asset_id, mime_type=mime_type)

    bulk_update_enrichment_level(session, [reference_id], new_level)
    session.commit()

    return new_level