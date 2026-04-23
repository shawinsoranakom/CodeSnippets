async def update_deployment(
    deployment_id: DeploymentIdPath,
    session: DbSession,
    payload: DeploymentUpdateRequest,
    current_user: CurrentActiveUser,
):
    deployment_row, deployment_adapter, deployment_mapper, provider_key = await resolve_adapter_mapper_from_deployment(
        deployment_id=deployment_id,
        user_id=current_user.id,
        db=session,
    )
    deployment_row_id = deployment_row.id
    deployment_resource_key = deployment_row.resource_key
    deployment_provider_account_id = deployment_row.deployment_provider_account_id
    adapter_payload = await deployment_mapper.resolve_deployment_update(
        user_id=current_user.id,
        deployment_db_id=deployment_row_id,
        db=session,
        payload=payload,
    )
    added_flow_version_ids, remove_flow_version_ids = resolve_flow_version_patch_for_update(
        deployment_mapper=deployment_mapper,
        payload=payload,
    )
    await validate_project_scoped_flow_version_ids(
        flow_version_ids=list(dict.fromkeys([*added_flow_version_ids, *remove_flow_version_ids])),
        user_id=current_user.id,
        project_id=deployment_row.project_id,
        db=session,
    )
    with handle_adapter_errors(mapper=deployment_mapper), deployment_provider_scope(deployment_provider_account_id):
        update_result: DeploymentUpdateResult = await deployment_adapter.update(
            deployment_id=deployment_resource_key,
            payload=adapter_payload,
            user_id=current_user.id,
            db=session,
        )
    try:
        existing_attachments = await list_deployment_attachments_for_flow_version_ids(
            session,
            user_id=current_user.id,
            deployment_id=deployment_row_id,
            flow_version_ids=added_flow_version_ids,
        )
        already_attached = {a.flow_version_id for a in existing_attachments}
        newly_added_flow_version_ids = [fv for fv in added_flow_version_ids if fv not in already_attached]
        added_snapshot_bindings = resolve_added_snapshot_bindings_for_update(
            deployment_mapper=deployment_mapper,
            added_flow_version_ids=newly_added_flow_version_ids,
            result=update_result,
        )
        await apply_flow_version_patch_attachments(
            user_id=current_user.id,
            deployment_row_id=deployment_row_id,
            added_snapshot_bindings=added_snapshot_bindings,
            remove_flow_version_ids=remove_flow_version_ids,
            db=session,
        )

        update_kwargs: dict = {}
        if payload.name is not None and payload.name != deployment_row.name:
            update_kwargs["name"] = payload.name
        if _field_was_explicitly_set(payload, "description"):
            if payload.description != deployment_row.description:
                update_kwargs["description"] = payload.description
        elif payload.description is not None and payload.description != deployment_row.description:
            update_kwargs["description"] = payload.description
        if update_kwargs:
            deployment_row = await update_deployment_db(
                session,
                deployment=deployment_row,
                **update_kwargs,
            )

        await session.commit()
    except Exception as exc:
        # Provider was already mutated by deployment_adapter.update above.
        # Roll back the session to discard any pending DB changes (or reset
        # it from the "inactive" state after a failed commit) so the mapper
        # can query the original attachment rows and build a compensating
        # payload.
        await session.rollback()
        await rollback_provider_update(
            deployment_adapter=deployment_adapter,
            deployment_mapper=deployment_mapper,
            deployment_db_id=deployment_row_id,
            deployment_resource_key=deployment_resource_key,
            deployment_provider_account_id=deployment_provider_account_id,
            user_id=current_user.id,
            db=session,
        )
        if isinstance(exc, AttachmentConflictError):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        raise

    return deployment_mapper.shape_deployment_update_result(
        update_result,
        deployment_row,
        provider_key=provider_key,
    )