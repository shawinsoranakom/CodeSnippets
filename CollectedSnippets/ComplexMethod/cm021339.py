async def test_action(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test for actions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(
        entry.entity_id,
        HVACMode.COOL,
        {
            const.ATTR_HVAC_MODES: [HVACMode.COOL, HVACMode.OFF],
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY],
        },
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_hvac_mode",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "set_hvac_mode",
                        "hvac_mode": HVACMode.OFF,
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_preset_mode",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "set_preset_mode",
                        "preset_mode": const.PRESET_AWAY,
                    },
                },
            ]
        },
    )

    set_hvac_mode_calls = async_mock_service(hass, "climate", "set_hvac_mode")
    set_preset_mode_calls = async_mock_service(hass, "climate", "set_preset_mode")

    hass.bus.async_fire("test_event_set_hvac_mode")
    await hass.async_block_till_done()
    assert len(set_hvac_mode_calls) == 1
    assert len(set_preset_mode_calls) == 0

    hass.bus.async_fire("test_event_set_preset_mode")
    await hass.async_block_till_done()
    assert len(set_hvac_mode_calls) == 1
    assert len(set_preset_mode_calls) == 1

    assert set_hvac_mode_calls[0].domain == DOMAIN
    assert set_hvac_mode_calls[0].service == "set_hvac_mode"
    assert set_hvac_mode_calls[0].data == {
        "entity_id": entry.entity_id,
        "hvac_mode": const.HVACMode.OFF,
    }
    assert set_preset_mode_calls[0].domain == DOMAIN
    assert set_preset_mode_calls[0].service == "set_preset_mode"
    assert set_preset_mode_calls[0].data == {
        "entity_id": entry.entity_id,
        "preset_mode": const.PRESET_AWAY,
    }