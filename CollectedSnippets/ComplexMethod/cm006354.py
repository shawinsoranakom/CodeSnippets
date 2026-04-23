async def list_deployments_page(
    db: AsyncSession,
    *,
    user_id: UUID,
    deployment_provider_account_id: UUID,
    offset: int,
    limit: int,
    flow_version_ids: list[UUID] | None = None,
    project_id: UUID | None = None,
) -> list[tuple[Deployment, int, list[tuple[UUID, str | None]]]]:
    """Return a page of deployments with attachment counts and matched attachments.

    The third tuple element contains ``(flow_version_id, provider_snapshot_id)``
    pairs for attachments that matched the ``flow_version_ids`` filter (empty
    list when no filter is active).
    """
    if offset < 0:
        msg = "offset must be greater than or equal to 0"
        raise ValueError(msg)
    if limit <= 0:
        msg = "limit must be greater than 0"
        raise ValueError(msg)

    attachment_counts_subquery = (
        select(
            col(FlowVersionDeploymentAttachment.deployment_id).label("deployment_id"),
            func.count(func.distinct(FlowVersionDeploymentAttachment.flow_version_id)).label("attached_count"),
        )
        .where(FlowVersionDeploymentAttachment.user_id == user_id)
        .group_by(FlowVersionDeploymentAttachment.deployment_id)
        .subquery()
    )
    stmt = (
        select(
            Deployment,
            func.coalesce(attachment_counts_subquery.c.attached_count, 0).label("attached_count"),
        )
        .outerjoin(attachment_counts_subquery, attachment_counts_subquery.c.deployment_id == Deployment.id)
        .where(
            Deployment.user_id == user_id,
            Deployment.deployment_provider_account_id == deployment_provider_account_id,
        )
    )
    if project_id is not None:
        stmt = stmt.where(Deployment.project_id == project_id)
    if flow_version_ids:
        matched_deployments_subquery = (
            select(FlowVersionDeploymentAttachment.deployment_id)
            .where(
                FlowVersionDeploymentAttachment.user_id == user_id,
                col(FlowVersionDeploymentAttachment.flow_version_id).in_(flow_version_ids),
            )
            .group_by(FlowVersionDeploymentAttachment.deployment_id)
            .subquery()
        )
        stmt = stmt.join(
            matched_deployments_subquery,
            matched_deployments_subquery.c.deployment_id == Deployment.id,
        )
    stmt = stmt.order_by(col(Deployment.created_at).desc(), col(Deployment.id).desc()).offset(offset).limit(limit)
    rows = (await db.exec(stmt)).all()
    deployment_rows = [(deployment, int(attached_count or 0)) for deployment, attached_count in rows]
    if not flow_version_ids or not deployment_rows:
        return [(deployment, attached_count, []) for deployment, attached_count in deployment_rows]

    deployment_ids = [deployment.id for deployment, _ in deployment_rows]
    matched_rows = (
        await db.exec(
            select(
                FlowVersionDeploymentAttachment.deployment_id,
                FlowVersionDeploymentAttachment.flow_version_id,
                FlowVersionDeploymentAttachment.provider_snapshot_id,
            ).where(
                FlowVersionDeploymentAttachment.user_id == user_id,
                col(FlowVersionDeploymentAttachment.deployment_id).in_(deployment_ids),
                col(FlowVersionDeploymentAttachment.flow_version_id).in_(flow_version_ids),
            )
        )
    ).all()
    matched_by_deployment: dict[UUID, list[tuple[UUID, str | None]]] = {}
    for deployment_id, flow_version_id, provider_snapshot_id in matched_rows:
        entries = matched_by_deployment.setdefault(deployment_id, [])
        pair = (flow_version_id, provider_snapshot_id)
        if pair not in entries:
            entries.append(pair)

    return [
        (
            deployment,
            attached_count,
            matched_by_deployment.get(deployment.id, []),
        )
        for deployment, attached_count in deployment_rows
    ]