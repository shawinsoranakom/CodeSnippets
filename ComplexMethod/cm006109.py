def test_watsonx_mapper_shapes_config_list_result_with_full_slot_validation() -> None:
    mapper = WatsonxOrchestrateDeploymentMapper()
    now = datetime.now(tz=timezone.utc)
    result = ConfigListResult(
        configs=[
            ConfigListItem(
                id="conn-1",
                name="cfg-1",
                created_at=now,
                updated_at=now,
                provider_data={"type": "key_value_creds", "environment": "draft"},
            ),
            ConfigListItem(id="conn-2", name="cfg-2", provider_data={"type": "key_value_creds", "environment": "live"}),
        ],
        provider_result={"deployment_id": " dep-1 ", "tool_ids": ["tool-1", "  "]},
    )

    shaped = mapper.shape_config_list_result(result, page=1, size=1)

    assert shaped.total is None
    assert shaped.page is None
    assert shaped.size is None
    assert shaped.provider_data is not None
    assert "deployment_id" not in shaped.provider_data
    assert "tool_ids" not in shaped.provider_data
    assert shaped.provider_data["page"] == 1
    assert shaped.provider_data["size"] == 1
    assert shaped.provider_data["total"] == 2
    assert len(shaped.provider_data["connections"]) == 1
    assert shaped.provider_data["connections"][0]["app_id"] == "cfg-1"
    assert shaped.provider_data["connections"][0]["connection_id"] == "conn-1"
    assert shaped.provider_data["connections"][0]["type"] == "key_value_creds"
    assert shaped.provider_data["connections"][0]["environment"] == "draft"
    assert set(shaped.provider_data["connections"][0].keys()) == {
        "app_id",
        "connection_id",
        "type",
        "environment",
    }