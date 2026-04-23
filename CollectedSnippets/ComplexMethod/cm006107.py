def test_watsonx_mapper_provider_list_entry_flattens_provider_data_and_uses_id() -> None:
    mapper = WatsonxOrchestrateDeploymentMapper()
    now = datetime.now(tz=timezone.utc)
    item = SimpleNamespace(
        id="agent-1",
        name="Agent 1",
        type=DeploymentType.AGENT,
        description="desc",
        created_at=now,
        updated_at=now,
        provider_data={"tool_ids": ["tool-1", "  ", "tool-2"], "environment": "draft"},
    )

    shaped = mapper._shape_provider_deployment_list_entry(item)

    assert shaped["id"] == "agent-1"
    assert shaped["name"] == "Agent 1"
    assert shaped["type"] == DeploymentType.AGENT.value
    assert shaped["description"] == "desc"
    assert shaped["created_at"] == now.isoformat().replace("+00:00", "Z")
    assert shaped["updated_at"] == now.isoformat().replace("+00:00", "Z")
    assert shaped["tool_ids"] == ["tool-1", "tool-2"]
    assert shaped["environment"] == "draft"
    assert "provider_data" not in shaped
    assert "resource_key" not in shaped