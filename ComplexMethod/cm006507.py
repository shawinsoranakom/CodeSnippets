def resolve_added_snapshot_bindings_for_update(
    *,
    deployment_mapper: BaseDeploymentMapper,
    added_flow_version_ids: list[UUID],
    result: DeploymentUpdateResult,
) -> list[tuple[UUID, str]]:
    if not added_flow_version_ids:
        return []
    bindings = deployment_mapper.util_update_snapshot_bindings(
        result=result,
    )
    bindings_by_source_ref = bindings.to_source_ref_map()
    expected_source_ref_to_flow_version_id: dict[str, UUID] = {
        str(flow_version_id): flow_version_id for flow_version_id in added_flow_version_ids
    }

    unexpected_source_refs = sorted(
        source_ref for source_ref in bindings_by_source_ref if source_ref not in expected_source_ref_to_flow_version_id
    )
    if unexpected_source_refs:
        msg = f"Unexpected source_ref in update snapshot bindings: {unexpected_source_refs}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)

    snapshot_bindings: list[tuple[UUID, str]] = []
    missing_source_refs: list[str] = []
    for source_ref, flow_version_id in expected_source_ref_to_flow_version_id.items():
        snapshot_id = bindings_by_source_ref.get(source_ref)
        if snapshot_id is None:
            missing_source_refs.append(source_ref)
            continue
        snapshot_bindings.append((flow_version_id, snapshot_id))
    if missing_source_refs:
        msg = f"Missing snapshot bindings for added flow versions on update: {missing_source_refs}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)
    return snapshot_bindings