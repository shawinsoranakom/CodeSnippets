async def update_snapshot(
    provider_snapshot_id: Annotated[
        str,
        Path(min_length=1, description="Provider-owned snapshot identifier (e.g. WXO tool_id)."),
    ],
    *,
    body: SnapshotUpdateRequest,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Replace an existing provider snapshot's content with a new flow version.

    Resolves the deployment context from the attachment record linked to
    ``provider_snapshot_id``.  Only Langflow-tracked snapshots (those with
    a ``flow_version_deployment_attachment`` row) can be updated.
    """
    from langflow.services.database.models.deployment.crud import get_deployment as get_deployment_row
    from langflow.services.database.models.flow_version.crud import get_flow_version_entry

    snapshot_id = provider_snapshot_id.strip()

    attachment = await get_attachment_by_provider_snapshot_id(
        session,
        user_id=current_user.id,
        provider_snapshot_id=snapshot_id,
    )
    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No attachment found for provider_snapshot_id '{snapshot_id}'.",
        )

    deployment = await get_deployment_row(
        session,
        user_id=current_user.id,
        deployment_id=attachment.deployment_id,
    )
    if deployment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment for attachment (deployment_id={attachment.deployment_id}) not found.",
        )

    flow_version = await get_flow_version_entry(
        session,
        version_id=body.flow_version_id,
        user_id=current_user.id,
    )
    if flow_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flow version '{body.flow_version_id}' not found.",
        )
    if flow_version.data is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Flow version '{body.flow_version_id}' has no data.",
        )

    provider_account = await get_owned_provider_account_or_404(
        provider_id=deployment.deployment_provider_account_id,
        user_id=current_user.id,
        db=session,
    )
    deployment_adapter = resolve_deployment_adapter(provider_account.provider_key)
    deployment_mapper = get_deployment_mapper(provider_account.provider_key)

    from langflow.services.database.models.flow.model import Flow

    flow_row = await session.get(Flow, flow_version.flow_id)

    flow_artifact = deployment_mapper.resolve_snapshot_update_artifact(
        flow_version=flow_version,
        flow_row=flow_row,
        deployment=deployment,
    )

    with (
        handle_adapter_errors(mapper=deployment_mapper),
        deployment_provider_scope(deployment.deployment_provider_account_id),
    ):
        await deployment_adapter.update_snapshot(
            user_id=current_user.id,
            db=session,
            snapshot_id=snapshot_id,
            flow_artifact=flow_artifact,
        )

    # Provider mutation succeeded — update all local attachment rows that share
    # this provider snapshot id.
    # If the DB flush fails, attempt a best-effort compensating re-upload
    # of the previous flow version's artifact.
    # Concurrency note: rollback uses a single previously-read flow_version_id.
    # This assumes the snapshot->flow_version invariant held before this call.
    # Because the invariant is enforced in app logic (not a DB constraint),
    # concurrent writers can still race and violate that assumption.
    previous_flow_version_id = attachment.flow_version_id
    try:
        updated_rows = await update_flow_version_by_provider_snapshot_id(
            session,
            user_id=current_user.id,
            provider_snapshot_id=snapshot_id,
            flow_version_id=body.flow_version_id,
        )
        if updated_rows == 0:
            logger.warning(
                "Snapshot '%s' update changed zero attachment rows after provider mutation "
                "(user_id=%s, requested_flow_version_id=%s). Possible concurrent modification.",
                snapshot_id,
                current_user.id,
                body.flow_version_id,
            )
        await session.commit()
    except Exception:
        await session.rollback()
        logger.warning(
            "DB update/commit failed after provider snapshot update for snapshot '%s' "
            "(requested_flow_version_id=%s). Attempting compensating provider rollback.",
            snapshot_id,
            body.flow_version_id,
            exc_info=True,
        )
        try:
            prev_version = await get_flow_version_entry(
                session,
                version_id=previous_flow_version_id,
                user_id=current_user.id,
            )
            if prev_version and prev_version.data:
                prev_artifact = deployment_mapper.resolve_snapshot_update_artifact(
                    flow_version=prev_version,
                    flow_row=flow_row,
                    deployment=deployment,
                )
                with deployment_provider_scope(deployment.deployment_provider_account_id):
                    await deployment_adapter.update_snapshot(
                        user_id=current_user.id,
                        db=session,
                        snapshot_id=snapshot_id,
                        flow_artifact=prev_artifact,
                    )
                logger.info(
                    "Restored provider snapshot '%s' to previous flow_version_id=%s after DB commit failure.",
                    snapshot_id,
                    previous_flow_version_id,
                )
        except Exception:  # noqa: BLE001
            logger.warning(
                "Best-effort rollback failed for snapshot '%s'. "
                "Provider content reflects flow_version_id=%s but attachment "
                "records point to flow_version_id=%s. Manual reconciliation may be needed.",
                snapshot_id,
                body.flow_version_id,
                previous_flow_version_id,
                exc_info=True,
            )
        raise

    return SnapshotUpdateResponse(
        flow_version_id=body.flow_version_id,
        provider_snapshot_id=snapshot_id,
    )