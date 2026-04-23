async def ingest_files_to_knowledge_base(
    kb_name: str,
    current_user: CurrentActiveUser,
    files: Annotated[list[UploadFile], File(description="Files to ingest into the knowledge base")],
    source_name: Annotated[str, Form()] = "",
    chunk_size: Annotated[int, Form()] = 1000,
    chunk_overlap: Annotated[int, Form()] = 200,
    separator: Annotated[str, Form()] = "",
    column_config: Annotated[str, Form()] = "",
) -> dict[str, object] | TaskResponse:
    """Upload and ingest files directly into a knowledge base.

    This endpoint:
    1. Accepts file uploads
    2. Extracts text and chunks the content
    3. Creates embeddings using the KB's configured embedding model
    4. Stores the vectors in the knowledge base
    """
    try:
        settings = get_settings_service().settings
        max_file_size_upload = settings.max_file_size_upload

        files_data = []

        for uploaded_file in files:
            file_size = uploaded_file.size
            if file_size > max_file_size_upload * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"File {uploaded_file.filename} exceeds the maximum upload size of {max_file_size_upload}MB",
                )
            content = await uploaded_file.read()
            files_data.append((uploaded_file.filename or "unknown", content))

        kb_path = _resolve_kb_path(kb_name, current_user)

        # Parse and persist column_config from FormData if provided
        if column_config:
            try:
                column_config_parsed = json.loads(column_config)
                if isinstance(column_config_parsed, list):
                    # Update embedding_metadata.json
                    cc_metadata_path = kb_path / "embedding_metadata.json"
                    if cc_metadata_path.exists():
                        existing_meta = json.loads(cc_metadata_path.read_text())
                        existing_meta["column_config"] = column_config_parsed
                        cc_metadata_path.write_text(json.dumps(existing_meta, indent=2))
                    # Write schema.json for text-metric helpers
                    schema_data = [{**col, "data_type": "string"} for col in column_config_parsed]
                    schema_path = kb_path / "schema.json"
                    schema_path.write_text(json.dumps(schema_data, indent=2))
            except (json.JSONDecodeError, TypeError):
                await logger.awarning("Malformed column_config received, using existing schema")

        # Read embedding metadata (Pass fast=False to ensure legacy KBs are migrated/detected)
        metadata = KBAnalysisHelper.get_metadata(kb_path, fast=False)
        if not metadata:
            raise HTTPException(
                status_code=400,
                detail="Knowledge base missing embedding configuration. Please create a new KB or reconfigure it.",
            )

        embedding_provider = metadata.get("embedding_provider")
        embedding_model = metadata.get("embedding_model")

        # Handle backward compatibility: generate asset_id if not present
        asset_id_str = metadata.get("id")
        if not asset_id_str:
            # Generate new UUID for older KBs without asset_id
            asset_id = uuid.uuid4()
            # Persist the new ID to metadata
            metadata_path = kb_path / "embedding_metadata.json"
            if metadata_path.exists():
                try:
                    embedding_metadata = json.loads(metadata_path.read_text())
                    embedding_metadata["id"] = str(asset_id)
                    metadata_path.write_text(json.dumps(embedding_metadata, indent=2))
                except (OSError, json.JSONDecodeError):
                    await logger.awarning("Could not update metadata with asset_id")
        else:
            asset_id = uuid.UUID(asset_id_str)

        if not embedding_provider or not embedding_model:
            raise HTTPException(status_code=400, detail="Invalid embedding configuration")

        # Get services and create job before async/sync split
        job_service = get_job_service()
        job_id = uuid.uuid4()

        # Create job record in database for both async and sync paths
        await job_service.create_job(
            job_id=job_id,
            flow_id=job_id,
            job_type=JobType.INGESTION,
            asset_id=asset_id,
            asset_type="knowledge_base",
            user_id=current_user.id,
        )

        # Always use async path: fire and forget the ingestion logic wrapped in status updates
        task_service = get_task_service()
        await task_service.fire_and_forget_task(
            job_service.execute_with_status,
            job_id=job_id,
            run_coro_func=KBIngestionHelper.perform_ingestion,
            kb_name=kb_name,
            kb_path=kb_path,
            files_data=files_data,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator=separator,
            source_name=source_name,
            current_user=current_user,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            task_job_id=job_id,
            job_service=job_service,
        )
        return TaskResponse(id=str(job_id), href=f"/task/{job_id}")

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("Error ingesting files to knowledge base: %s", e)
        raise HTTPException(status_code=500, detail="Error ingesting files to knowledge base.") from e