def test_watsonx_mapper_shapes_flow_version_list_result_with_enrichment() -> None:
    mapper = WatsonxOrchestrateDeploymentMapper()
    attached_at = datetime.now(tz=timezone.utc)
    flow_version_id = uuid4()
    flow_id = uuid4()

    rows = [
        (
            SimpleNamespace(provider_snapshot_id="tool-1", created_at=attached_at),
            SimpleNamespace(id=flow_version_id, flow_id=flow_id, version_number=3),
            "Flow A",
        )
    ]
    snapshot_result = SnapshotListResult(
        snapshots=[
            SnapshotItem(
                id="tool-1",
                name="Tool 1",
                provider_data={"connections": {"cfg-1": "conn-1"}},
            )
        ]
    )

    shaped = mapper.shape_flow_version_list_result(
        rows=rows,
        snapshot_result=snapshot_result,
        page=1,
        size=20,
        total=1,
    )

    assert shaped.total == 1
    assert len(shaped.flow_versions) == 1
    assert shaped.flow_versions[0].id == flow_version_id
    assert shaped.flow_versions[0].flow_id == flow_id
    assert shaped.flow_versions[0].flow_name == "Flow A"
    assert shaped.flow_versions[0].version_number == 3
    assert shaped.flow_versions[0].attached_at == attached_at
    assert shaped.flow_versions[0].provider_snapshot_id == "tool-1"
    assert shaped.flow_versions[0].provider_data == {"app_ids": ["cfg-1"], "tool_name": "Tool 1"}