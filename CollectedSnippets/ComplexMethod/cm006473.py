async def activate_version(
    flow_id: UUID,
    version_id: UUID,
    current_user: CurrentActiveUser,
    session: DbSession,
    *,
    save_draft: Annotated[bool, Query()] = True,
) -> FlowRead:
    flow = await _get_user_flow(session, flow_id, current_user.id)

    # Verify version entry belongs to this flow
    try:
        target_entry = await get_flow_version_entry_or_raise(session, version_id, current_user.id, flow_id=flow_id)
    except FlowVersionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Version entry not found") from exc

    # Guard against activating a version with no data (check before auto-snapshot)
    if target_entry.data is None:
        raise HTTPException(status_code=400, detail="Cannot activate a version with no data")

    # Capture copies of both data dicts before the savepoint to avoid stale
    # reads if pruning inside create_flow_version_entry deletes old entries.
    try:
        current_data = copy.deepcopy(flow.data) if save_draft else None
        target_data = copy.deepcopy(target_entry.data)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Flow data could not be copied. The data may be corrupted.",
        ) from exc

    # Wrap auto-snapshot + flow overwrite in a single savepoint for atomicity.
    # If the flow update fails, the auto-snapshot is also rolled back.
    try:
        async with session.begin_nested():
            if save_draft and current_data is not None:
                await create_flow_version_entry(
                    session,
                    flow_id=flow.id,
                    user_id=current_user.id,
                    data=current_data,
                    description=f"Auto-saved before activating v{target_entry.version_number}",
                )

            flow.data = target_data
            flow.updated_at = datetime.now(timezone.utc)

            session.add(flow)
            await session.flush()
    except FlowVersionError as exc:
        raise _translate_version_error(exc) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Could not activate version — the flow was modified concurrently. Please try again.",
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Database error while activating version. Please try again.",
        ) from exc

    await logger.adebug("Activated version %s (%s) for flow %s", version_id, f"v{target_entry.version_number}", flow_id)

    return FlowRead.model_validate(flow, from_attributes=True)