def batch_insert_seed_assets(
    session: Session,
    specs: list[SeedAssetSpec],
    owner_id: str = "",
) -> BulkInsertResult:
    """Seed assets from filesystem specs in batch.

    Each spec is a dict with keys:
      - abs_path: str
      - size_bytes: int
      - mtime_ns: int
      - info_name: str
      - tags: list[str]
      - fname: Optional[str]

    This function orchestrates:
    1. Insert seed Assets (hash=NULL)
    2. Claim references with ON CONFLICT DO NOTHING on file_path
    3. Query to find winners (paths where our asset_id was inserted)
    4. Delete Assets for losers (path already claimed by another asset)
    5. Insert tags and metadata for successfully inserted references

    Returns:
        BulkInsertResult with inserted_refs, won_paths, lost_paths
    """
    if not specs:
        return BulkInsertResult(inserted_refs=0, won_paths=0, lost_paths=0)

    current_time = get_utc_now()
    asset_rows: list[AssetRow] = []
    reference_rows: list[ReferenceRow] = []
    path_to_asset_id: dict[str, str] = {}
    asset_id_to_ref_data: dict[str, dict] = {}
    absolute_path_list: list[str] = []

    for spec in specs:
        absolute_path = os.path.abspath(spec["abs_path"])
        asset_id = str(uuid.uuid4())
        reference_id = str(uuid.uuid4())
        absolute_path_list.append(absolute_path)
        path_to_asset_id[absolute_path] = asset_id

        mime_type = spec.get("mime_type")
        asset_rows.append(
            {
                "id": asset_id,
                "hash": spec.get("hash"),
                "size_bytes": spec["size_bytes"],
                "mime_type": mime_type,
                "created_at": current_time,
            }
        )

        # Build user_metadata from extracted metadata or fallback to filename
        extracted_metadata = spec.get("metadata")
        if extracted_metadata:
            user_metadata: dict[str, Any] | None = extracted_metadata.to_user_metadata()
        elif spec["fname"]:
            user_metadata = {"filename": spec["fname"]}
        else:
            user_metadata = None

        reference_rows.append(
            {
                "id": reference_id,
                "asset_id": asset_id,
                "file_path": absolute_path,
                "mtime_ns": spec["mtime_ns"],
                "owner_id": owner_id,
                "name": spec["info_name"],
                "preview_id": None,
                "user_metadata": user_metadata,
                "job_id": spec.get("job_id"),
                "created_at": current_time,
                "updated_at": current_time,
                "last_access_time": current_time,
            }
        )

        asset_id_to_ref_data[asset_id] = {
            "reference_id": reference_id,
            "tags": spec["tags"],
            "filename": spec["fname"],
            "extracted_metadata": extracted_metadata,
        }

    bulk_insert_assets(session, asset_rows)

    # Filter reference rows to only those whose assets were actually inserted
    # (assets with duplicate hashes are silently dropped by ON CONFLICT DO NOTHING)
    inserted_asset_ids = get_existing_asset_ids(
        session, [r["asset_id"] for r in reference_rows]
    )
    reference_rows = [r for r in reference_rows if r["asset_id"] in inserted_asset_ids]

    bulk_insert_references_ignore_conflicts(session, reference_rows)
    restore_references_by_paths(session, absolute_path_list)
    winning_paths = get_references_by_paths_and_asset_ids(session, path_to_asset_id)

    inserted_paths = {
        path
        for path in absolute_path_list
        if path_to_asset_id[path] in inserted_asset_ids
    }
    losing_paths = inserted_paths - winning_paths
    lost_asset_ids = [path_to_asset_id[path] for path in losing_paths]

    if lost_asset_ids:
        delete_assets_by_ids(session, lost_asset_ids)

    if not winning_paths:
        return BulkInsertResult(
            inserted_refs=0,
            won_paths=0,
            lost_paths=len(losing_paths),
        )

    # Get reference IDs for winners
    winning_ref_ids = [
        asset_id_to_ref_data[path_to_asset_id[path]]["reference_id"]
        for path in winning_paths
    ]
    inserted_ref_ids = get_reference_ids_by_ids(session, winning_ref_ids)

    tag_rows: list[TagRow] = []
    metadata_rows: list[MetadataRow] = []

    if inserted_ref_ids:
        for path in winning_paths:
            asset_id = path_to_asset_id[path]
            ref_data = asset_id_to_ref_data[asset_id]
            ref_id = ref_data["reference_id"]

            if ref_id not in inserted_ref_ids:
                continue

            for tag in ref_data["tags"]:
                tag_rows.append(
                    {
                        "asset_reference_id": ref_id,
                        "tag_name": tag,
                        "origin": "automatic",
                        "added_at": current_time,
                    }
                )

            # Use extracted metadata for meta rows if available
            extracted_metadata = ref_data.get("extracted_metadata")
            if extracted_metadata:
                metadata_rows.extend(extracted_metadata.to_meta_rows(ref_id))
            elif ref_data["filename"]:
                # Fallback: just store filename
                metadata_rows.append(
                    {
                        "asset_reference_id": ref_id,
                        "key": "filename",
                        "ordinal": 0,
                        "val_str": ref_data["filename"],
                        "val_num": None,
                        "val_bool": None,
                        "val_json": None,
                    }
                )

    bulk_insert_tags_and_meta(session, tag_rows=tag_rows, meta_rows=metadata_rows)

    return BulkInsertResult(
        inserted_refs=len(inserted_ref_ids),
        won_paths=len(winning_paths),
        lost_paths=len(losing_paths),
    )