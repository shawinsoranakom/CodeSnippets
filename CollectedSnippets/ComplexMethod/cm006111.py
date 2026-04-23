def test_watsonx_mapper_exposes_reconciliation_resolvers() -> None:
    mapper = WatsonxOrchestrateDeploymentMapper()
    add_id = uuid4()
    unbind_only_id = uuid4()
    remove_id = uuid4()
    patch = mapper.util_flow_version_patch(
        DeploymentUpdateRequest(
            provider_data={
                "llm": TEST_WXO_LLM,
                "connections": [],
                "upsert_flows": [
                    {
                        "flow_version_id": str(add_id),
                        "add_app_ids": ["app-one"],
                        "remove_app_ids": [],
                    },
                    {
                        "flow_version_id": str(unbind_only_id),
                        "add_app_ids": [],
                        "remove_app_ids": ["app-one"],
                    },
                ],
                "remove_flows": [str(remove_id)],
            }
        )
    )
    assert isinstance(patch, FlowVersionPatch)
    add_ids, remove_ids = patch.add_flow_version_ids, patch.remove_flow_version_ids
    assert add_ids == [add_id]
    assert remove_ids == [remove_id]

    create_bindings = mapper.util_create_snapshot_bindings(
        result=DeploymentCreateResult(
            id="provider-id",
            provider_result={"tools_with_refs": [{"source_ref": "fv-1", "tool_id": "snap-1"}]},
        ),
    )
    assert isinstance(create_bindings, CreateSnapshotBindings)
    assert create_bindings.to_source_ref_map() == {"fv-1": "snap-1"}

    created_ids = mapper.util_created_snapshot_ids(
        result=DeploymentUpdateResult(
            id="provider-id",
            provider_result={
                "created_snapshot_ids": ["snap-1"],
                "added_snapshot_bindings": [{"source_ref": str(add_id), "tool_id": "snap-1", "created": True}],
            },
        ),
    )
    assert isinstance(created_ids, CreatedSnapshotIds)
    assert created_ids.ids == ["snap-1"]
    update_bindings = mapper.util_update_snapshot_bindings(
        result=DeploymentUpdateResult(
            id="provider-id",
            provider_result={
                "added_snapshot_bindings": [{"source_ref": str(add_id), "tool_id": "snap-1", "created": True}],
            },
        ),
    )
    assert isinstance(update_bindings, UpdateSnapshotBindings)
    assert update_bindings.to_source_ref_map() == {str(add_id): "snap-1"}