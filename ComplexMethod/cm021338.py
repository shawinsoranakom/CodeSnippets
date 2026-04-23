async def test_if_fires_on_state_change(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for turn_on and turn_off triggers firing."""
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
            const.ATTR_HVAC_ACTION: HVACAction.IDLE,
            const.ATTR_CURRENT_HUMIDITY: 23,
            const.ATTR_CURRENT_TEMPERATURE: 18,
        },
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
                        "type": "hvac_mode_changed",
                        "to": HVACMode.AUTO,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "hvac_mode_changed"},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "current_temperature_changed",
                        "above": 20,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "current_temperature_changed"},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "current_humidity_changed",
                        "below": 10,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "current_humidity_changed"},
                    },
                },
            ]
        },
    )

    # Fake that the HVAC mode is changing
    hass.states.async_set(
        entry.entity_id,
        HVACMode.AUTO,
        {
            const.ATTR_HVAC_ACTION: HVACAction.COOLING,
            const.ATTR_CURRENT_HUMIDITY: 23,
            const.ATTR_CURRENT_TEMPERATURE: 18,
        },
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "hvac_mode_changed"

    # Fake that the temperature is changing
    hass.states.async_set(
        entry.entity_id,
        HVACMode.AUTO,
        {
            const.ATTR_HVAC_ACTION: HVACAction.COOLING,
            const.ATTR_CURRENT_HUMIDITY: 23,
            const.ATTR_CURRENT_TEMPERATURE: 23,
        },
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "current_temperature_changed"

    # Fake that the humidity is changing
    hass.states.async_set(
        entry.entity_id,
        HVACMode.AUTO,
        {
            const.ATTR_HVAC_ACTION: HVACAction.COOLING,
            const.ATTR_CURRENT_HUMIDITY: 7,
            const.ATTR_CURRENT_TEMPERATURE: 23,
        },
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[2].data["some"] == "current_humidity_changed"