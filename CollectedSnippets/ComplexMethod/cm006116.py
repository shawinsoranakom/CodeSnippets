def test_base_mapper_shapes_deployment_update_result() -> None:
    mapper = BaseDeploymentMapper()
    deployment_id = uuid4()
    provider_account_id = uuid4()
    timestamp = datetime.now(tz=timezone.utc)
    result = DeploymentUpdateResult(id="provider-id", provider_result={"ok": True})
    deployment_row = SimpleNamespace(
        id=deployment_id,
        name="Deployment Name",
        description="desc",
        deployment_type=DeploymentType.AGENT,
        resource_key="provider-id",
        created_at=timestamp,
        updated_at=timestamp,
        deployment_provider_account_id=provider_account_id,
    )

    shaped = mapper.shape_deployment_update_result(
        result,
        deployment_row,
        provider_key="test-provider",
    )

    assert shaped.id == deployment_id
    assert shaped.provider_id == provider_account_id
    assert shaped.provider_key == "test-provider"
    assert shaped.name == "Deployment Name"
    assert shaped.description == "desc"
    assert shaped.type == DeploymentType.AGENT
    assert shaped.provider_data == {"ok": True}