async def test_if_fires_on_state_change_legacy(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
    mock_update_entities: list[MockUpdateEntity],
) -> None:
    """Test for turn_on and turn_off triggers firing."""
    setup_test_component_platform(hass, DOMAIN, mock_update_entities)
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get("update.update_available")
    entity_registry.async_update_entity(entry.entity_id, device_id=device_entry.id)

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.entity_id,
                        "type": "turned_off",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "no_update {{ trigger.platform }}"
                                " - {{ trigger.entity_id }}"
                                " - {{ trigger.from_state.state }}"
                                " - {{ trigger.to_state.state }}"
                                " - {{ trigger.for }}"
                            )
                        },
                    },
                },
            ]
        },
    )
    await hass.async_block_till_done()
    state = hass.states.get("update.update_available")
    assert state
    assert state.state == STATE_ON
    assert not service_calls

    hass.states.async_set("update.update_available", STATE_OFF)
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert (
        service_calls[0].data["some"]
        == "no_update device - update.update_available - on - off - None"
    )