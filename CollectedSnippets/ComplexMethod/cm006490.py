async def _new_flow(
    *,
    session: AsyncSession,
    flow: FlowCreate,
    user_id: UUID,
    storage_service: StorageService,
    flow_id: UUID | None = None,
    fail_on_endpoint_conflict: bool = False,
    validate_folder: bool = False,
):
    """Create or upsert a flow.

    Args:
        session: Database session.
        flow: Flow creation data.
        user_id: Owner of the new flow.
        storage_service: Service for filesystem operations.
        flow_id: Allows PUT upsert to create flows with a specific ID for syncing between instances.
        fail_on_endpoint_conflict: PUT should fail predictably on conflicts rather than silently renaming.
        validate_folder: Validates folder_id exists and belongs to user when upserting from external sources.
    """
    try:
        await _verify_fs_path(flow.fs_path, user_id, storage_service)

        if validate_folder and flow.folder_id is not None:
            folder = (
                await session.exec(select(Folder).where(Folder.id == flow.folder_id, Folder.user_id == user_id))
            ).first()
            if not folder:
                raise HTTPException(status_code=400, detail="Folder not found")

        # Set user_id (ignore any user_id from body for security)
        flow.user_id = user_id
        flow.name = await _deduplicate_flow_name(session, flow.name, user_id)

        if flow.endpoint_name:
            flow.endpoint_name = await _deduplicate_endpoint_name(
                session, flow.endpoint_name, user_id, fail_on_conflict=fail_on_endpoint_conflict
            )

        # Exclude the id field from FlowCreate so that Flow.id (UUID, non-optional)
        # always gets its default_factory uuid4 unless we explicitly override it below.
        db_flow = Flow.model_validate(flow.model_dump(exclude={"id"}))

        # Apply the stable ID: explicit flow_id param (PUT upsert) takes precedence,
        # then flow.id (stable import from FlowCreate), then the uuid4 default.
        effective_id = flow_id if flow_id is not None else flow.id
        if effective_id is not None:
            db_flow.id = effective_id

        db_flow.updated_at = datetime.now(timezone.utc)
        await _validate_and_assign_folder(session, db_flow, user_id)

        session.add(db_flow)
        await session.flush()
        await session.refresh(db_flow)
        await _save_flow_to_fs(db_flow, user_id, storage_service)

        return FlowRead.model_validate(db_flow, from_attributes=True)
    except Exception as e:
        if hasattr(e, "errors"):
            raise HTTPException(status_code=400, detail=str(e)) from e
        if isinstance(e, HTTPException):
            raise
        logger.exception("Error creating flow")
        raise HTTPException(status_code=500, detail="An internal error occurred while creating the flow.") from e