async def test_if_state(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for turn_on and turn_off conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_hvac_mode",
                            "hvac_mode": "cool",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_hvac_mode - {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event2"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_preset_mode",
                            "preset_mode": "away",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_preset_mode - {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
            ]
        },
    )

    # Should not fire, entity doesn't exist yet
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    hass.states.async_set(
        entry.entity_id,
        HVACMode.COOL,
        {
            const.ATTR_PRESET_MODE: const.PRESET_AWAY,
        },
    )

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "is_hvac_mode - event - test_event1"

    hass.states.async_set(
        entry.entity_id,
        HVACMode.AUTO,
        {
            const.ATTR_PRESET_MODE: const.PRESET_AWAY,
        },
    )

    # Should not fire
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    assert len(service_calls) == 1

    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()

    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "is_preset_mode - event - test_event2"

    hass.states.async_set(
        entry.entity_id,
        HVACMode.AUTO,
        {
            const.ATTR_PRESET_MODE: const.PRESET_HOME,
        },
    )

    # Should not fire
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    assert len(service_calls) == 2