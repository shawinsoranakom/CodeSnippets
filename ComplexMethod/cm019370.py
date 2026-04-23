async def test_service_preset_mode_frost_guard_thermostat(
    hass: HomeAssistant, config_entry: MockConfigEntry, netatmo_auth: AsyncMock
) -> None:
    """Test service with frost guard preset for thermostats."""
    with selected_platforms([Platform.CLIMATE]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_livingroom = "climate.livingroom"

    assert hass.states.get(climate_entity_livingroom).state == "auto"
    assert (
        hass.states.get(climate_entity_livingroom).attributes["preset_mode"] == "away"
    )

    # Test service setting the preset mode to "frost guard"
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: climate_entity_livingroom,
            ATTR_PRESET_MODE: PRESET_FROST_GUARD,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Fake webhook thermostat mode change to "Frost Guard"
    response = {
        "event_type": "therm_mode",
        "home": {"id": "91763b24c43d3e344f424e8b", "therm_mode": "hg"},
        "mode": "hg",
        "previous_mode": "schedule",
        "push_type": "home_event_changed",
    }
    await simulate_webhook(hass, webhook_id, response)

    assert hass.states.get(climate_entity_livingroom).state == "auto"
    assert (
        hass.states.get(climate_entity_livingroom).attributes["preset_mode"]
        == "frost_guard"
    )

    # Test service setting the preset mode to "frost guard"
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: climate_entity_livingroom,
            ATTR_PRESET_MODE: PRESET_SCHEDULE,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    # Test webhook thermostat mode change to "Schedule"
    response = {
        "event_type": "therm_mode",
        "home": {"id": "91763b24c43d3e344f424e8b", "therm_mode": "schedule"},
        "mode": "schedule",
        "previous_mode": "hg",
        "push_type": "home_event_changed",
    }
    await simulate_webhook(hass, webhook_id, response)

    assert hass.states.get(climate_entity_livingroom).state == "auto"
    assert (
        hass.states.get(climate_entity_livingroom).attributes["preset_mode"] == "away"
    )