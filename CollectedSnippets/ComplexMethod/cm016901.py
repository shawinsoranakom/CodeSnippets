def sync_references_with_filesystem(
    session,
    root: RootType,
    collect_existing_paths: bool = False,
    update_missing_tags: bool = False,
) -> set[str] | None:
    """Reconcile asset references with filesystem for a root.

    - Toggle needs_verify per reference using mtime/size stat check
    - For hashed assets with at least one stat-unchanged ref: delete stale missing refs
    - For seed assets with all refs missing: delete Asset and its references
    - Optionally add/remove 'missing' tags based on stat check in this root
    - Optionally return surviving absolute paths

    Args:
        session: Database session
        root: Root type to scan
        collect_existing_paths: If True, return set of surviving file paths
        update_missing_tags: If True, update 'missing' tags based on file status

    Returns:
        Set of surviving absolute paths if collect_existing_paths=True, else None
    """
    prefixes = get_prefixes_for_root(root)
    if not prefixes:
        return set() if collect_existing_paths else None

    rows = get_references_for_prefixes(
        session, prefixes, include_missing=update_missing_tags
    )

    by_asset: dict[str, _AssetAccumulator] = {}
    for row in rows:
        acc = by_asset.get(row.asset_id)
        if acc is None:
            acc = {"hash": row.asset_hash, "size_db": row.size_bytes, "refs": []}
            by_asset[row.asset_id] = acc

        stat_unchanged = False
        try:
            exists = True
            stat_unchanged = verify_file_unchanged(
                mtime_db=row.mtime_ns,
                size_db=acc["size_db"],
                stat_result=os.stat(row.file_path, follow_symlinks=True),
            )
        except FileNotFoundError:
            exists = False
        except PermissionError:
            exists = True
            logging.debug("Permission denied accessing %s", row.file_path)
        except OSError as e:
            exists = False
            logging.debug("OSError checking %s: %s", row.file_path, e)

        acc["refs"].append(
            {
                "ref_id": row.reference_id,
                "file_path": row.file_path,
                "exists": exists,
                "stat_unchanged": stat_unchanged,
                "needs_verify": row.needs_verify,
            }
        )

    to_set_verify: list[str] = []
    to_clear_verify: list[str] = []
    stale_ref_ids: list[str] = []
    to_mark_missing: list[str] = []
    to_clear_missing: list[str] = []
    survivors: set[str] = set()

    for aid, acc in by_asset.items():
        a_hash = acc["hash"]
        refs = acc["refs"]
        any_unchanged = any(r["stat_unchanged"] for r in refs)
        all_missing = all(not r["exists"] for r in refs)

        for r in refs:
            if not r["exists"]:
                to_mark_missing.append(r["ref_id"])
                continue
            if r["stat_unchanged"]:
                to_clear_missing.append(r["ref_id"])
                if r["needs_verify"]:
                    to_clear_verify.append(r["ref_id"])
            if not r["stat_unchanged"] and not r["needs_verify"]:
                to_set_verify.append(r["ref_id"])

        if a_hash is None:
            if refs and all_missing:
                delete_orphaned_seed_asset(session, aid)
            else:
                for r in refs:
                    if r["exists"]:
                        survivors.add(os.path.abspath(r["file_path"]))
            continue

        if any_unchanged:
            for r in refs:
                if not r["exists"]:
                    stale_ref_ids.append(r["ref_id"])
            if update_missing_tags:
                try:
                    remove_missing_tag_for_asset_id(session, asset_id=aid)
                except Exception as e:
                    logging.warning(
                        "Failed to remove missing tag for asset %s: %s", aid, e
                    )
        elif update_missing_tags:
            try:
                add_missing_tag_for_asset_id(session, asset_id=aid, origin="automatic")
            except Exception as e:
                logging.warning("Failed to add missing tag for asset %s: %s", aid, e)

        for r in refs:
            if r["exists"]:
                survivors.add(os.path.abspath(r["file_path"]))

    delete_references_by_ids(session, stale_ref_ids)
    stale_set = set(stale_ref_ids)
    to_mark_missing = [ref_id for ref_id in to_mark_missing if ref_id not in stale_set]
    bulk_update_is_missing(session, to_mark_missing, value=True)
    bulk_update_is_missing(session, to_clear_missing, value=False)
    bulk_update_needs_verify(session, to_set_verify, value=True)
    bulk_update_needs_verify(session, to_clear_verify, value=False)

    return survivors if collect_existing_paths else None