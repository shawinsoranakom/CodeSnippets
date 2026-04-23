def test_base_mapper_shapes_flow_version_list_result() -> None:
    mapper = BaseDeploymentMapper()
    attached_at = datetime.now(tz=timezone.utc)
    flow_version_id = uuid4()
    flow_id = uuid4()
    rows = [
        (
            SimpleNamespace(provider_snapshot_id=" tool-1 ", created_at=attached_at),
            SimpleNamespace(id=flow_version_id, flow_id=flow_id, version_number=4),
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
        page=2,
        size=5,
        total=7,
    )

    assert shaped.page == 2
    assert shaped.size == 5
    assert shaped.total == 7
    assert len(shaped.flow_versions) == 1
    assert shaped.flow_versions[0].id == flow_version_id
    assert shaped.flow_versions[0].flow_id == flow_id
    assert shaped.flow_versions[0].flow_name == "Flow A"
    assert shaped.flow_versions[0].version_number == 4
    assert shaped.flow_versions[0].attached_at == attached_at
    assert shaped.flow_versions[0].provider_snapshot_id == "tool-1"
    assert shaped.flow_versions[0].provider_data is None