async def create_deployment(
    session: DbSession,
    payload: DeploymentCreateRequest,
    current_user: CurrentActiveUser,
):
    provider_id = payload.provider_id
    provider_account = await get_owned_provider_account_or_404(
        provider_id=provider_id,
        user_id=current_user.id,
        db=session,
    )
    # fail fast if the deployment name already exists
    # we could have races but that is more
    # acceptable than provider-side rollback failure
    if await deployment_name_exists(
        session,
        user_id=current_user.id,
        deployment_provider_account_id=provider_id,
        name=payload.name,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A deployment named '{payload.name}' already exists. "
            "Please choose a different name or delete the existing deployment first.",
        )

    deployment_adapter = resolve_deployment_adapter(provider_account.provider_key)
    deployment_mapper = get_deployment_mapper(provider_account.provider_key)
    existing_resource_key = deployment_mapper.util_existing_deployment_resource_key_for_create(payload)
    if existing_resource_key is not None:
        existing_deployment = await get_deployment_by_resource_key(
            session,
            user_id=current_user.id,
            deployment_provider_account_id=provider_id,
            resource_key=str(existing_resource_key),
        )
        if existing_deployment is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"The agent '{existing_resource_key}' is already managed by Langflow. "
                "Update it to make changes, or delete the existing deployment first.",
            )
    should_mutate_existing_resource = (
        existing_resource_key is not None
        and deployment_mapper.util_should_mutate_provider_for_existing_deployment_create(payload)
    )
    should_create_provider_resource = existing_resource_key is None
    project_id = await resolve_project_id_for_deployment_create(payload=payload, user_id=current_user.id, db=session)
    flow_version_ids = deployment_mapper.util_create_flow_version_ids(payload)
    await validate_project_scoped_flow_version_ids(
        flow_version_ids=flow_version_ids,
        user_id=current_user.id,
        project_id=project_id,
        db=session,
    )
    if should_create_provider_resource:
        adapter_payload = await deployment_mapper.resolve_deployment_create(
            user_id=current_user.id,
            project_id=project_id,
            db=session,
            payload=payload,
        )
        with handle_adapter_errors(mapper=deployment_mapper), deployment_provider_scope(provider_id):
            provider_create_result = await deployment_adapter.create(
                user_id=current_user.id,
                payload=adapter_payload,
                db=session,
            )
    else:
        provider_create_result = deployment_mapper.util_create_result_from_existing_resource(
            existing_resource_key=str(existing_resource_key),
        )
        if should_mutate_existing_resource:
            adapter_payload = await deployment_mapper.resolve_deployment_update_for_existing_create(
                user_id=current_user.id,
                project_id=project_id,
                db=session,
                payload=payload,
            )
            with handle_adapter_errors(mapper=deployment_mapper), deployment_provider_scope(provider_id):
                provider_update_result: DeploymentUpdateResult = await deployment_adapter.update(
                    deployment_id=existing_resource_key,
                    payload=adapter_payload,
                    user_id=current_user.id,
                    db=session,
                )
            provider_create_result = deployment_mapper.util_create_result_from_existing_update(
                existing_resource_key=str(existing_resource_key),
                result=provider_update_result,
            )
    # if we get here, the deployment was created successfully in the provider
    # so we need to create the deployment row and attach the flow versions
    # in the DB
    try:
        deployment_row = await create_deployment_db(
            session,
            user_id=current_user.id,
            project_id=project_id,
            deployment_provider_account_id=provider_id,
            resource_key=str(provider_create_result.id),
            name=payload.name,
            deployment_type=payload.type,
            description=payload.description or None,
        )

        snapshot_id_by_flow_version_id: dict[UUID, str] = {}
        if flow_version_ids:
            snapshot_id_by_flow_version_id = resolve_snapshot_map_for_create(
                deployment_mapper=deployment_mapper,
                result=provider_create_result,
                flow_version_ids=flow_version_ids,
            )
        await attach_flow_versions(
            flow_version_ids=flow_version_ids,
            user_id=current_user.id,
            deployment_row_id=deployment_row.id,
            snapshot_id_by_flow_version_id=snapshot_id_by_flow_version_id,
            db=session,
        )

        await session.commit()
    except Exception as exc:
        # Compensate: delete the provider resource so it doesn't become orphaned.
        # Only the deployment resource itself is deleted (e.g. the WXO agent).
        # Secondary resources (snapshots/tools, configs) may remain orphaned --
        # this is intentional because snapshots/configs may be shared across deployments,
        # making cascade-delete unsafe.
        await session.rollback()
        if should_create_provider_resource:
            await rollback_provider_create(
                deployment_adapter=deployment_adapter,
                provider_id=provider_id,
                resource_id=provider_create_result.id,
                provider_result=provider_create_result.provider_result,
                user_id=current_user.id,
                db=session,
            )
        elif should_mutate_existing_resource:
            await rollback_provider_create(
                deployment_adapter=deployment_adapter,
                provider_id=provider_id,
                resource_id=str(existing_resource_key),
                provider_result=provider_create_result.provider_result,
                allow_delete_fallback=False,
                user_id=current_user.id,
                db=session,
            )
        if isinstance(exc, AttachmentConflictError):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        raise
    return deployment_mapper.shape_deployment_create_result(
        provider_create_result, deployment_row, provider_key=provider_account.provider_key
    )