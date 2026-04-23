async def list_deployments(
    provider_id: DeploymentProviderAccountIdQuery,
    session: DbSession,
    current_user: CurrentActiveUser,
    params: Annotated[Params, Depends(deployment_pagination_params)],
    deployment_type: Annotated[DeploymentType | None, Query()] = None,
    *,
    load_from_provider: Annotated[
        bool,
        Query(
            description=("When true, list deployments directly from the provider (bypassing Langflow deployment rows).")
        ),
    ] = False,
    flow_version_ids: Annotated[
        FlowVersionIdsQuery,
        Query(
            description=(
                "Optional Langflow flow version ids (pass as repeated query params, "
                "e.g. ?flow_version_ids=id1&flow_version_ids=id2). When provided, "
                "deployments are filtered to those with at least one matching "
                "attachment (OR semantics across ids). "
                "Mutually exclusive with flow_ids."
            )
        ),
    ] = None,
    flow_ids: Annotated[
        FlowIdsQuery,
        Query(
            description=(
                "Optional flow ids (pass as repeated query params, "
                "e.g. ?flow_ids=id1). Currently limited to 1 value. "
                "When provided, deployments are filtered to those attached "
                "to versions of the specified flow(s). "
                "Mutually exclusive with flow_version_ids."
            )
        ),
    ] = None,
    project_id: ProjectIdQuery = None,
):
    if flow_ids and flow_version_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="flow_ids and flow_version_ids are mutually exclusive.",
        )
    if load_from_provider and flow_version_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="flow_version_ids filtering is not supported when loading deployments directly from the provider.",
        )
    if load_from_provider and flow_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="flow_ids filtering is not supported when loading deployments directly from the provider.",
        )
    if load_from_provider and project_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="project_id filtering is not supported when loading deployments directly from the provider.",
        )

    effective_flow_version_ids = flow_version_ids
    if flow_ids:
        resolved = await flow_version_ids_for_flows(session, flow_ids=flow_ids, user_id=current_user.id)
        if not resolved:
            return DeploymentListResponse(
                deployments=[], page=params.page, size=params.size, total=0, deployment_type=deployment_type
            )
        effective_flow_version_ids = resolved

    provider_account = await get_owned_provider_account_or_404(
        provider_id=provider_id, user_id=current_user.id, db=session
    )
    deployment_adapter = resolve_deployment_adapter(provider_account.provider_key)
    deployment_mapper = get_deployment_mapper(provider_account.provider_key)
    if load_from_provider:
        with handle_adapter_errors(mapper=deployment_mapper), deployment_provider_scope(provider_id):
            provider_view = await deployment_adapter.list(
                user_id=current_user.id,
                db=session,
                params=None if deployment_type is None else DeploymentListParams(deployment_types=[deployment_type]),
            )
        return deployment_mapper.shape_deployment_list_result(provider_view)

    with handle_adapter_errors(mapper=deployment_mapper), deployment_provider_scope(provider_id):
        rows_with_counts, total = await list_deployments_synced(
            deployment_adapter=deployment_adapter,
            deployment_mapper=deployment_mapper,
            user_id=current_user.id,
            provider_id=provider_id,
            db=session,
            page=params.page,
            size=params.size,
            deployment_type=deployment_type,
            flow_version_ids=effective_flow_version_ids,
            project_id=project_id,
        )
    deployments = deployment_mapper.shape_deployment_list_items(
        rows_with_counts=rows_with_counts,
        # include flow_version_ids in list items only when
        # flow_version_ids or flow_ids filtering is active.
        # (empty lists are rejected by validation)
        has_flow_filter=bool(flow_version_ids or flow_ids),
        provider_key=provider_account.provider_key,
    )
    return DeploymentListResponse(
        deployments=deployments,
        page=params.page,
        size=params.size,
        total=total,
        provider_data=None,
    )