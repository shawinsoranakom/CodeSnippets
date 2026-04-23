def test_watsonx_mapper_shapes_snapshot_list_result_without_nested_provider_data() -> None:
    mapper = WatsonxOrchestrateDeploymentMapper()
    result = SnapshotListResult(
        snapshots=[
            SnapshotItem(
                id="tool-1",
                name="Tool 1",
                provider_data={"connections": {"cfg-1": "conn-1"}},
            )
        ],
        provider_result={"deployment_id": "dep-1"},
    )

    shaped = mapper.shape_snapshot_list_result(result, page=1, size=20)

    assert shaped.total is None
    assert shaped.page is None
    assert shaped.size is None
    assert shaped.provider_data is not None
    assert "deployment_id" not in shaped.provider_data
    assert shaped.provider_data["page"] == 1
    assert shaped.provider_data["size"] == 20
    assert shaped.provider_data["total"] == 1
    assert shaped.provider_data["tools"] == [
        {
            "id": "tool-1",
            "name": "Tool 1",
            "connections": {"cfg-1": "conn-1"},
        }
    ]
    assert "provider_data" not in shaped.provider_data["tools"][0]