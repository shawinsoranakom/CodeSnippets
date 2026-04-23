async def test_bad_formatted_automations(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_config_store: dict[str, Any],
) -> None:
    """Test that we handle automations without ID."""
    with patch.object(config, "SECTIONS", [automation]):
        await async_setup_component(hass, "config", {})

    assert sorted(hass.states.async_entity_ids("automation")) == []

    client = await hass_client()

    orig_data = [
        {
            # No ID
            "action": {"event": "hello"}
        },
        {"id": "moon"},
    ]
    hass_config_store["automations.yaml"] = orig_data

    resp = await client.post(
        "/api/config/automation/config/moon",
        data=json.dumps({"triggers": [], "actions": [], "conditions": []}),
    )
    await hass.async_block_till_done()
    assert sorted(hass.states.async_entity_ids("automation")) == [
        "automation.automation_1",
    ]
    assert hass.states.get("automation.automation_1").state == STATE_ON

    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"result": "ok"}

    # Verify ID added
    new_data = hass_config_store["automations.yaml"]
    assert "id" in new_data[0]
    assert new_data[1] == {
        "id": "moon",
        "triggers": [],
        "conditions": [],
        "actions": [],
    }