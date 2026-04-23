async def test_if_fires_on_state_between(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for value triggers firing."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, STATE_UNKNOWN, {"device_class": "battery"})

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
                        "type": "battery_level",
                        "above": 10,
                        "below": 20,
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
                }
            ]
        },
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    hass.states.async_set(entry.entity_id, 9)
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    hass.states.async_set(entry.entity_id, 11)
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert (
        service_calls[0].data["some"]
        == f"bat_low device - {entry.entity_id} - 9 - 11 - None"
    )

    hass.states.async_set(entry.entity_id, 21)
    await hass.async_block_till_done()
    assert len(service_calls) == 1

    hass.states.async_set(entry.entity_id, 19)
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert (
        service_calls[1].data["some"]
        == f"bat_low device - {entry.entity_id} - 21 - 19 - None"
    )