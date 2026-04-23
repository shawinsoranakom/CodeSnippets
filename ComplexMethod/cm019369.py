async def test_webhook_event_handling_thermostats(
    hass: HomeAssistant, config_entry: MockConfigEntry, netatmo_auth: AsyncMock
) -> None:
    """Test service and webhook event handling with thermostats."""
    with selected_platforms([Platform.CLIMATE]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_livingroom = "climate.livingroom"

    assert hass.states.get(climate_entity_livingroom).state == "auto"
    assert (
        hass.states.get(climate_entity_livingroom).attributes["preset_mode"] == "away"
    )
    assert hass.states.get(climate_entity_livingroom).attributes["temperature"] == 12

    # Test service setting the temperature
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_TEMPERATURE: 21},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Fake webhook thermostat manual set point
    response = {
        "room_id": "2746182631",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2746182631",
                    "name": "Livingroom",
                    "type": "livingroom",
                    "therm_setpoint_mode": "manual",
                    "therm_setpoint_temperature": 21,
                    "therm_setpoint_end_time": 1612734552,
                }
            ],
            "modules": [
                {"id": "12:34:56:00:01:ae", "name": "Livingroom", "type": "NATherm1"}
            ],
        },
        "mode": "manual",
        "event_type": "set_point",
        "temperature": 21,
        "push_type": "display_change",
    }
    await simulate_webhook(hass, webhook_id, response)

    assert hass.states.get(climate_entity_livingroom).state == "heat"
    assert (
        hass.states.get(climate_entity_livingroom).attributes["preset_mode"] == "away"
    )
    assert hass.states.get(climate_entity_livingroom).attributes["temperature"] == 21

    # Test service setting the HVAC mode to "heat"
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Fake webhook thermostat mode change to "Max"
    response = {
        "room_id": "2746182631",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2746182631",
                    "name": "Livingroom",
                    "type": "livingroom",
                    "therm_setpoint_mode": "max",
                    "therm_setpoint_end_time": 1612749189,
                }
            ],
            "modules": [
                {"id": "12:34:56:00:01:ae", "name": "Livingroom", "type": "NATherm1"}
            ],
        },
        "mode": "max",
        "event_type": "set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(hass, webhook_id, response)

    assert hass.states.get(climate_entity_livingroom).state == "heat"
    assert hass.states.get(climate_entity_livingroom).attributes["temperature"] == 30

    # Test service setting the HVAC mode to "off"
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Fake webhook turn thermostat off
    response = {
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2746182631",
                    "name": "Livingroom",
                    "type": "livingroom",
                    "therm_setpoint_mode": "off",
                }
            ],
            "modules": [
                {"id": "12:34:56:00:01:ae", "name": "Livingroom", "type": "NATherm1"}
            ],
        },
        "mode": "off",
        "event_type": "set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(hass, webhook_id, response)

    assert hass.states.get(climate_entity_livingroom).state == "off"

    # Test service setting the HVAC mode to "auto"
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_HVAC_MODE: HVACMode.AUTO},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Fake webhook thermostat mode cancel set point
    response = {
        "room_id": "2746182631",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2746182631",
                    "name": "Livingroom",
                    "type": "livingroom",
                    "therm_setpoint_mode": "home",
                }
            ],
            "modules": [
                {"id": "12:34:56:00:01:ae", "name": "Livingroom", "type": "NATherm1"}
            ],
        },
        "mode": "home",
        "event_type": "cancel_set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(hass, webhook_id, response)

    assert hass.states.get(climate_entity_livingroom).state == "auto"
    assert (
        hass.states.get(climate_entity_livingroom).attributes["preset_mode"] == "away"
    )