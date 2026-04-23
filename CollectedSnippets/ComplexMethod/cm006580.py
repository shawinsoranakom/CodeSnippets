def test_entity_specific_fields_are_scoped_to_own_params_classes() -> None:
    deployment_fields = set(DeploymentListParams.model_fields)
    config_fields = set(ConfigListParams.model_fields)
    snapshot_fields = set(SnapshotListParams.model_fields)

    assert "deployment_types" in deployment_fields
    assert "snapshot_ids" in deployment_fields
    assert "config_ids" in deployment_fields

    assert "config_ids" in config_fields
    assert "snapshot_ids" not in config_fields
    assert "deployment_types" not in config_fields

    assert "snapshot_ids" in snapshot_fields
    assert "config_ids" not in snapshot_fields
    assert "deployment_types" not in snapshot_fields