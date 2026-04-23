async def create_knowledge_base(
    request: CreateKnowledgeBaseRequest,
    current_user: CurrentActiveUser,
) -> KnowledgeBaseInfo:
    """Create a new knowledge base with embedding configuration."""
    try:
        kb_root_path = KBStorageHelper.get_root_path()
        kb_user = current_user.username
        kb_name = request.name.strip().replace(" ", "_")
        # Validate KB name
        if not kb_name or len(kb_name) < MIN_KB_NAME_LENGTH:
            raise HTTPException(status_code=400, detail="Knowledge base name must be at least 3 characters")

        # Security: resolve paths and validate containment to prevent path traversal attacks.
        # A crafted kb_name like "../victim/evil" or an absolute path like "/tmp/evil" must be
        # rejected before any directory is created.
        kb_user_path = (kb_root_path / kb_user).resolve()
        kb_path = (kb_user_path / kb_name).resolve()
        _validate_kb_path_containment(kb_user_path, kb_path, kb_name, kb_user)

        # Check if KB already exists
        if kb_path.exists():
            raise HTTPException(status_code=409, detail=f"Knowledge base '{kb_name}' already exists")

        # Create KB directory
        kb_path.mkdir(parents=True, exist_ok=True)
        kb_id = uuid.uuid4()

        # Initialize Chroma storage and collection immediately
        # This ensures files exist for read operations and avoids 'readonly' errors later
        try:
            client = KBStorageHelper.get_fresh_chroma_client(kb_path)
            client.create_collection(name=kb_name)
        except (OSError, ValueError, chromadb.errors.ChromaError) as e:
            logger.warning("Initial Chroma setup for %s failed: %s", kb_name, e)
        finally:
            client = None
            KBStorageHelper.release_chroma_resources(kb_path)

        # Serialize column_config for persistence
        column_config_dicts = None
        if request.column_config:
            column_config_dicts = [item.model_dump() for item in request.column_config]

        # Save full embedding metadata to prevent immediate backfill
        embedding_metadata = {
            "id": str(kb_id),
            "embedding_provider": request.embedding_provider,
            "embedding_model": request.embedding_model,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "chunks": 0,
            "words": 0,
            "characters": 0,
            "avg_chunk_size": 0.0,
            "size": 0,
            "column_config": column_config_dicts,
        }
        metadata_path = kb_path / "embedding_metadata.json"
        metadata_path.write_text(json.dumps(embedding_metadata, indent=2))

        # Write schema.json for text-metric helpers (get_text_columns)
        if column_config_dicts:
            schema_data = [{**col, "data_type": "string"} for col in column_config_dicts]
            schema_path = kb_path / "schema.json"
            schema_path.write_text(json.dumps(schema_data, indent=2))

        return KnowledgeBaseInfo(
            id=str(kb_id),
            dir_name=kb_name,
            name=kb_name.replace("_", " "),
            embedding_provider=request.embedding_provider,
            embedding_model=request.embedding_model,
            size=0,
            words=0,
            characters=0,
            chunks=0,
            avg_chunk_size=0.0,
            column_config=column_config_dicts,
        )

    except HTTPException:
        raise
    except Exception as e:
        # Clean up if something went wrong
        if kb_path.exists():
            KBStorageHelper.delete_storage(kb_path, kb_name)
        await logger.aerror("Error creating knowledge base: %s", e)
        raise HTTPException(status_code=500, detail="Internal error creating knowledge base") from e