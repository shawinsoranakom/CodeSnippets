async def list_deployments_synced(
    *,
    deployment_adapter: DeploymentServiceProtocol,
    deployment_mapper: BaseDeploymentMapper,
    user_id: UUID,
    provider_id: UUID,
    db: DbSession,
    page: int,
    size: int,
    deployment_type: DeploymentType | None,
    flow_version_ids: list[UUID] | None = None,
    project_id: UUID | None = None,
) -> tuple[list[tuple[Deployment, int, list[tuple[UUID, str | None]]]], int]:
    """Return a page of deployments, deleting any DB rows the provider doesn't recognise.

    Fetches DB rows in batches, sends each batch's resource keys to the
    provider for validation, and deletes stale rows inline. The cursor does
    not advance for deleted rows (deletion shifts subsequent offsets down).
    """
    accepted: list[tuple[Deployment, int, list[tuple[UUID, str | None]]]] = []
    cursor = page_offset(page, size)
    guard = 0
    while len(accepted) < size and guard < (size * 4 + 20):
        guard += 1
        batch = await list_deployments_page(
            db,
            user_id=user_id,
            deployment_provider_account_id=provider_id,
            offset=cursor,
            limit=size - len(accepted),
            flow_version_ids=flow_version_ids,
            project_id=project_id,
        )
        if not batch:
            break

        known = await fetch_provider_resource_keys(
            deployment_adapter=deployment_adapter,
            user_id=user_id,
            provider_id=provider_id,
            db=db,
            resource_keys=[row.resource_key for row, _, _ in batch],
            deployment_type=deployment_type,
        )

        for row, attached_count, matched_flow_versions in batch:
            if row.resource_key not in known:
                if deployment_type is not None and row.deployment_type != deployment_type:
                    cursor += 1
                    continue
                logger.warning(
                    "Deployment %s (resource_key=%s) not found on provider %s — deleting stale row",
                    row.id,
                    row.resource_key,
                    provider_id,
                )
                await delete_deployment_by_id(db, user_id=user_id, deployment_id=row.id)
                continue
            accepted.append((row, attached_count, matched_flow_versions))
            cursor += 1

    # Phase 2: snapshot-level sync.
    # Ask the mapper which attachment snapshot IDs are provider-verifiable,
    # verify them in a single batched provider call, and delete stale rows.
    # Best-effort — a provider outage should not block the list response.
    if accepted:
        try:
            deployment_ids_for_sync = [row.id for row, _count, _matched in accepted]
            all_attachments = await list_attachments_by_deployment_ids(
                db, user_id=user_id, deployment_ids=deployment_ids_for_sync
            )
            corrected_counts = await sync_provider_attachment_snapshots(
                deployment_adapter=deployment_adapter,
                deployment_mapper=deployment_mapper,
                user_id=user_id,
                provider_id=provider_id,
                db=db,
                attachments=all_attachments,
                deployment_ids=deployment_ids_for_sync,
            )
            if corrected_counts is not None:
                accepted = [(row, corrected_counts[row.id], matched) for row, _attached_count, matched in accepted]
            # else: no attachments carry a provider-verifiable snapshot ID,
            # so there is nothing to check against the provider. The
            # original attached_count from the DB is kept as-is.
        except Exception:  # noqa: BLE001
            logger.warning(
                "Snapshot-level sync failed for list_deployments_synced; returning unverified attachment counts",
                exc_info=True,
            )

    total = await count_deployments_by_provider(
        db,
        user_id=user_id,
        deployment_provider_account_id=provider_id,
        flow_version_ids=flow_version_ids,
        project_id=project_id,
    )
    return accepted, total