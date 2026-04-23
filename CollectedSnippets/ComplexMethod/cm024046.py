async def test_if_fires_on_state_change(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
    mock_binary_sensor_entities: dict[str, MockBinarySensor],
) -> None:
    """Test for on and off triggers firing."""
    setup_test_component_platform(hass, DOMAIN, mock_binary_sensor_entities.values())
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_binary_sensor_entities["battery"].unique_id,
        device_id=device_entry.id,
    )

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
                        "entity_id": entry.id,
                        "type": "bat_low",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "bat_low {{ trigger.platform }}"
                                " - {{ trigger.entity_id }}"
                                " - {{ trigger.from_state.state }}"
                                " - {{ trigger.to_state.state }}"
                                " - {{ trigger.for }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "not_bat_low",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "not_bat_low {{ trigger.platform }}"
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
    assert hass.states.get(entry.entity_id).state == STATE_ON
    assert len(service_calls) == 0

    hass.states.async_set(entry.entity_id, STATE_OFF)
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert (
        service_calls[0].data["some"]
        == f"not_bat_low device - {entry.entity_id} - on - off - None"
    )

    hass.states.async_set(entry.entity_id, STATE_ON)
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert (
        service_calls[1].data["some"]
        == f"bat_low device - {entry.entity_id} - off - on - None"
    )