async def test_delete_automation(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    entity_registry: er.EntityRegistry,
    hass_config_store: dict[str, Any],
) -> None:
    """Test deleting an automation."""

    assert len(entity_registry.entities) == 2

    with patch.object(config, "SECTIONS", [automation]):
        assert await async_setup_component(hass, "config", {})

    assert sorted(hass.states.async_entity_ids("automation")) == [
        "automation.automation_0",
        "automation.automation_1",
    ]

    client = await hass_client()

    orig_data = [{"id": "sun"}, {"id": "moon"}]
    hass_config_store["automations.yaml"] = orig_data

    resp = await client.delete("/api/config/automation/config/sun")
    await hass.async_block_till_done()

    assert sorted(hass.states.async_entity_ids("automation")) == [
        "automation.automation_1",
    ]

    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"result": "ok"}

    assert hass_config_store["automations.yaml"] == [{"id": "moon"}]

    assert len(entity_registry.entities) == 1