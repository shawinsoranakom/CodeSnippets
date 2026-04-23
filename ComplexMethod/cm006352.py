async def create_flow_version_entry(
    session: AsyncSession,
    flow_id: UUID,
    user_id: UUID,
    data: dict | None,
    description: str | None = None,
) -> FlowVersion:
    """Create a version entry with retry on version number collision.

    NOTE: This function does NOT verify that user_id owns the flow.
    Callers are responsible for checking ownership before calling this.
    """
    entry: FlowVersion | None = None
    for attempt in range(MAX_VERSION_RETRIES):
        version_number = await get_next_version_number(session, flow_id)
        entry = FlowVersion(
            flow_id=flow_id,
            user_id=user_id,
            data=data,
            description=description,
            version_number=version_number,
        )
        try:
            async with session.begin_nested():
                session.add(entry)
                await session.flush()
                await session.refresh(entry)
            break
        except IntegrityError as exc:
            if "unique_flow_version_number" not in str(exc).lower():
                raise  # Not a version collision — don't retry
            if attempt == MAX_VERSION_RETRIES - 1:
                msg = (
                    f"Failed to create version entry for flow {flow_id} after "
                    f"{MAX_VERSION_RETRIES} retries due to version number conflicts"
                )
                raise FlowVersionConflictError(msg) from exc
            await logger.awarning(
                "Version number collision for flow %s (attempt %d/%d), retrying",
                flow_id,
                attempt + 1,
                MAX_VERSION_RETRIES,
            )
            entry = None
            continue

    if entry is None:
        msg = (
            f"Failed to create version entry for flow {flow_id} after "
            f"{MAX_VERSION_RETRIES} retries due to version number conflicts"
        )
        raise FlowVersionConflictError(msg)

    # Prune oldest non-deployed entries beyond the configured limit.
    # Versions attached to deployments are excluded from pruning to avoid
    # orphaning provider-side snapshots. This means the actual count can
    # exceed max_entries when many versions are deployed — acceptable
    # because deployed versions are actively in use.
    # NOTE: Concurrent snapshot requests for the same flow could both insert
    # before either prunes, temporarily exceeding the limit by one or more
    # entries. This is acceptable — the excess self-corrects on the next
    # snapshot.
    try:
        max_entries = get_settings_service().settings.max_flow_version_entries_per_flow
        deployed_version_ids = (
            select(FlowVersionDeploymentAttachment.flow_version_id)
            .where(
                col(FlowVersionDeploymentAttachment.flow_version_id).in_(
                    select(FlowVersion.id).where(FlowVersion.flow_id == flow_id)
                )
            )
            .distinct()
        )
        delete_older = delete(FlowVersion).where(
            FlowVersion.flow_id == flow_id,
            col(FlowVersion.id).not_in(deployed_version_ids),
            col(FlowVersion.id).in_(
                select(FlowVersion.id)
                .where(
                    FlowVersion.flow_id == flow_id,
                    col(FlowVersion.id).not_in(deployed_version_ids),
                )
                .order_by(col(FlowVersion.version_number).desc())
                .offset(max_entries)
            ),
        )
        result = await session.exec(delete_older)
        if hasattr(result, "rowcount") and result.rowcount:  # type: ignore[union-attr]
            await logger.adebug("Pruned %d old version entries for flow %s", result.rowcount, flow_id)  # type: ignore[union-attr]
    except SQLAlchemyError:
        # Pruning is best-effort: we don't fail the snapshot because pruning broke.
        # Logged at error level because repeated failures cause unbounded table growth
        # and may need operational attention.
        await logger.aerror(
            "Failed to prune old version entries for flow %s — version table may exceed configured limit",
            flow_id,
            exc_info=True,
        )

    return entry