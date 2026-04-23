async def get_deployment(
    deployment_id: DeploymentIdPath,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    deployment_row, deployment_adapter, deployment_mapper, provider_key = await resolve_adapter_mapper_from_deployment(
        deployment_id=deployment_id,
        user_id=current_user.id,
        db=session,
    )

    with deployment_provider_scope(deployment_row.deployment_provider_account_id):
        # Deployment-level sync: if the provider no longer has this deployment,
        # delete the stale DB row (FK CASCADE handles attachments) and return 404.
        try:
            deployment = await deployment_adapter.get(
                user_id=current_user.id,
                deployment_id=deployment_row.resource_key,
                db=session,
            )
        except DeploymentNotFoundError:
            logger.warning(
                "Deployment %s (resource_key=%s) not found on provider — deleting stale row",
                deployment_row.id,
                deployment_row.resource_key,
            )
            try:
                await delete_deployment_by_id(session, user_id=current_user.id, deployment_id=deployment_row.id)
                await session.commit()
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Failed to delete stale deployment row %s; returning 404 anyway",
                    deployment_row.id,
                    exc_info=True,
                )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found.") from None
        except DeploymentServiceError as exc:
            raise HTTPException(
                status_code=http_status_for_deployment_error(exc),
                detail=exc.message,
            ) from exc

        # Snapshot-level sync: verify that tracked provider_snapshot_ids still exist.
        # Best-effort — a provider outage should not block the GET response.
        try:
            attachments = await list_deployment_attachments(
                session, user_id=current_user.id, deployment_id=deployment_row.id
            )
            snapshot_ids_to_verify = deployment_mapper.util_snapshot_ids_to_verify(attachments)
            if snapshot_ids_to_verify:
                known_snapshots = await fetch_provider_snapshot_keys(
                    deployment_adapter=deployment_adapter,
                    user_id=current_user.id,
                    provider_id=deployment_row.deployment_provider_account_id,
                    db=session,
                    snapshot_ids=snapshot_ids_to_verify,
                )
                corrected_counts = await sync_attachment_snapshot_ids(
                    user_id=current_user.id,
                    deployment_ids=[deployment_row.id],
                    attachments=attachments,
                    known_snapshot_ids=known_snapshots,
                    db=session,
                )
                attached_count = corrected_counts[deployment_row.id]
            else:
                # No attachments carry a provider-verifiable snapshot ID, so
                # there is nothing to check against the provider.  The raw
                # DB attachment count is used as-is.
                attached_count = len(attachments)
        except Exception:  # noqa: BLE001
            logger.warning(
                "Snapshot-level sync failed for deployment %s; returning unverified attachment count",
                deployment_row.id,
                exc_info=True,
            )
            await session.rollback()  # clean up potentially dirty session
            try:
                attachments = await list_deployment_attachments(
                    session, user_id=current_user.id, deployment_id=deployment_row.id
                )
                attached_count = len(attachments)
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Fallback attachment count query also failed for deployment %s; defaulting to 0",
                    deployment_row.id,
                    exc_info=True,
                )
                attached_count = 0

    payload = deployment.model_dump(exclude_unset=True)
    raw_provider_data = payload.get("provider_data")
    provider_data = raw_provider_data if isinstance(raw_provider_data, dict) and raw_provider_data else None
    return DeploymentGetResponse(
        id=deployment_row.id,
        provider_id=deployment_row.deployment_provider_account_id,
        provider_key=provider_key,
        name=deployment_row.name,
        description=deployment_row.description,
        type=deployment_row.deployment_type,
        # Timestamps are local DB audit fields, not provider payload fields.
        created_at=deployment_row.created_at,
        updated_at=deployment_row.updated_at,
        provider_data=provider_data,
        resource_key=deployment_row.resource_key,
        attached_count=attached_count,
    )