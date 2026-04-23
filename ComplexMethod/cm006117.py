def test_base_mapper_exposes_reconciliation_resolvers() -> None:
    mapper = BaseDeploymentMapper()
    payload = DeploymentUpdateRequest(
        provider_data={"operations": []},
    )
    patch = mapper.util_flow_version_patch(payload)
    assert isinstance(patch, FlowVersionPatch)
    add_ids, remove_ids = patch.add_flow_version_ids, patch.remove_flow_version_ids
    assert add_ids == []
    assert remove_ids == []

    create_result = DeploymentCreateResult(
        id="provider-id",
        provider_result={"snapshot_bindings": [{"source_ref": "fv-1", "snapshot_id": "snap-1"}]},
    )
    bindings = mapper.util_create_snapshot_bindings(
        result=create_result,
    )
    assert isinstance(bindings, CreateSnapshotBindings)
    assert bindings.snapshot_bindings == []

    update_result = DeploymentUpdateResult(id="provider-id")
    created_ids = mapper.util_created_snapshot_ids(
        result=update_result,
    )
    assert isinstance(created_ids, CreatedSnapshotIds)
    assert created_ids.ids == []
    update_bindings = mapper.util_update_snapshot_bindings(
        result=update_result,
    )
    assert isinstance(update_bindings, UpdateSnapshotBindings)
    assert update_bindings.snapshot_bindings == []

    exec_result = ExecutionStatusResult(
        execution_id="e-1",
        deployment_id="dep-1",
        provider_result={"agent_id": "agent-1"},
    )
    assert mapper.util_resource_key_from_execution(exec_result) == "dep-1"