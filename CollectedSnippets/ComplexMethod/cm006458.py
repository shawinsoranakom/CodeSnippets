async def list_knowledge_bases(
    current_user: CurrentActiveUser,
    job_service: Annotated[JobService, Depends(get_job_service)],
) -> list[KnowledgeBaseInfo]:
    """List all available knowledge bases."""
    try:
        kb_root_path = KBStorageHelper.get_root_path()
        kb_path = kb_root_path / current_user.username

        if not kb_path.exists():
            return []

        knowledge_bases = []
        kb_ids_to_fetch = []  # Collect KB IDs for batch fetching

        # First pass: Load all KBs into memory
        for kb_dir in kb_path.iterdir():
            if not kb_dir.is_dir() or kb_dir.name.startswith("."):
                continue
            try:
                # Use deep update (fast=False) to ensure legacy KBs are migrated on first view
                metadata = KBAnalysisHelper.get_metadata(kb_dir, fast=False)

                # Extract KB ID from metadata (stored as string, convert to UUID)
                kb_id_str = metadata.get("id")
                if kb_id_str:
                    try:
                        kb_id_uuid = uuid.UUID(kb_id_str)
                        kb_ids_to_fetch.append(kb_id_uuid)
                    except (ValueError, AttributeError):
                        # If ID is invalid, skip job status lookup for this KB
                        kb_id_str = None

                chunks_count = metadata["chunks"]
                status = "ready" if chunks_count > 0 else "empty"
                failure_reason = None
                kb_info = KnowledgeBaseInfo(
                    id=kb_id_str or kb_dir.name,  # Fallback to directory name if no ID
                    dir_name=kb_dir.name,
                    name=kb_dir.name.replace("_", " "),
                    embedding_provider=metadata["embedding_provider"],
                    embedding_model=metadata["embedding_model"],
                    size=metadata["size"],
                    words=metadata["words"],
                    characters=metadata["characters"],
                    chunks=chunks_count,
                    avg_chunk_size=metadata["avg_chunk_size"],
                    chunk_size=metadata.get("chunk_size"),
                    chunk_overlap=metadata.get("chunk_overlap"),
                    separator=metadata.get("separator"),
                    status=status,
                    failure_reason=failure_reason,
                    last_job_id=None,
                    source_types=metadata.get("source_types", []),
                    column_config=metadata.get("column_config"),
                )
                knowledge_bases.append(kb_info)

            except OSError as _:
                # Log the exception and skip directories that can't be read
                await logger.aexception("Error reading knowledge base directory '%s'", kb_dir)
                continue

        # Second pass: Batch fetch all job statuses in a single query
        if kb_ids_to_fetch:
            latest_jobs = await job_service.get_latest_jobs_by_asset_ids(kb_ids_to_fetch)

            # Map job statuses back to knowledge bases
            # Normalize to frontend-expected values: ready, ingesting, failed, empty
            job_status_map = {
                "queued": "ingesting",
                "in_progress": "ingesting",
                "failed": "failed",
                "cancelled": "failed",
                "timed_out": "failed",
            }
            for kb_info in knowledge_bases:
                try:
                    kb_uuid = uuid.UUID(kb_info.id)
                    if kb_uuid in latest_jobs:
                        job = latest_jobs[kb_uuid]
                        raw_status = job.status.value if hasattr(job.status, "value") else str(job.status)
                        mapped = job_status_map.get(raw_status)
                        if mapped:
                            kb_info.status = mapped
                        # For "completed", keep the file-marker / chunk-count status already set
                        kb_info.last_job_id = str(job.job_id)
                except (ValueError, AttributeError):
                    # If KB ID is not a valid UUID, skip job status update
                    pass

    except Exception as e:
        await logger.aerror("Error listing knowledge bases: %s", e)
        raise HTTPException(status_code=500, detail="Error listing knowledge bases.") from e
    else:
        return knowledge_bases