async def _update_existing_flow(
    *,
    session: AsyncSession,
    existing_flow: Flow,
    flow: FlowCreate,
    current_user: User,
    storage_service: StorageService,
) -> FlowRead:
    """Update an existing flow (PUT update path).

    Similar to update_flow but:
    - Fails on name/endpoint_name conflict with OTHER flows (409)
    - Keeps existing folder_id if not provided in request
    """
    settings_service = get_settings_service()
    user_id = current_user.id

    # Validate fs_path if provided (use `is not None` to catch empty strings)
    if flow.fs_path is not None:
        await _verify_fs_path(flow.fs_path, user_id, storage_service)

    # Validate folder_id if provided
    if flow.folder_id is not None:
        folder = (
            await session.exec(select(Folder).where(Folder.id == flow.folder_id, Folder.user_id == user_id))
        ).first()
        if not folder:
            raise HTTPException(status_code=400, detail="Folder not found")

    # Check name uniqueness (excluding current flow)
    if flow.name and flow.name != existing_flow.name:
        name_conflict = (
            await session.exec(
                select(Flow).where(
                    Flow.name == flow.name,
                    Flow.user_id == user_id,
                    Flow.id != existing_flow.id,
                )
            )
        ).first()
        if name_conflict:
            raise HTTPException(status_code=409, detail="Name must be unique")

    # Check endpoint_name uniqueness (excluding current flow)
    if flow.endpoint_name and flow.endpoint_name != existing_flow.endpoint_name:
        endpoint_conflict = (
            await session.exec(
                select(Flow).where(
                    Flow.endpoint_name == flow.endpoint_name,
                    Flow.user_id == user_id,
                    Flow.id != existing_flow.id,
                )
            )
        ).first()
        if endpoint_conflict:
            raise HTTPException(status_code=409, detail="Endpoint name must be unique")

    # Build update data
    update_data = flow.model_dump(exclude_unset=True, exclude_none=True)

    # Preserve the existing endpoint unless the request explicitly clears it.
    if _endpoint_name_was_explicitly_cleared(flow):
        update_data["endpoint_name"] = None

    # Remove id and user_id from update data (security)
    update_data.pop("id", None)
    update_data.pop("user_id", None)

    # If folder_id not provided, keep existing
    if "folder_id" not in update_data or update_data.get("folder_id") is None:
        update_data.pop("folder_id", None)

    if settings_service.settings.remove_api_keys:
        update_data = remove_api_keys(update_data)

    _apply_update_data(existing_flow, update_data)

    webhook_component = get_webhook_component_in_flow(existing_flow.data or {})
    existing_flow.webhook = webhook_component is not None
    existing_flow.updated_at = datetime.now(timezone.utc)

    session.add(existing_flow)
    await session.flush()
    await session.refresh(existing_flow)
    await _save_flow_to_fs(existing_flow, user_id, storage_service)

    return FlowRead.model_validate(existing_flow, from_attributes=True)