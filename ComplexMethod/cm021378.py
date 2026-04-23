async def test_climate_set_temperature_turn_off_turn_on(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test Broadlink climate."""

    device = get_device("Guest room")
    mock_api = device.get_mock_api()
    mock_api.get_full_status.return_value = {
        "sensor": SensorMode.INNER_SENSOR_CONTROL.value,
        "power": 1,
        "auto_mode": 0,
        "active": 1,
        "room_temp": 22,
        "thermostat_temp": 23,
        "external_temp": 30,
    }
    mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_setup.entry.unique_id)}
    )
    entries = er.async_entries_for_device(entity_registry, device_entry.id)
    climates = [entry for entry in entries if entry.domain == Platform.CLIMATE]
    assert len(climates) == 1

    climate = climates[0]

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: climate.entity_id,
            ATTR_TEMPERATURE: "24",
        },
        blocking=True,
    )
    state = hass.states.get(climate.entity_id)

    assert mock_setup.api.set_temp.call_count == 1
    assert mock_setup.api.set_power.call_count == 0
    assert mock_setup.api.set_mode.call_count == 0
    assert state.attributes["temperature"] == 24

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: climate.entity_id,
        },
        blocking=True,
    )
    state = hass.states.get(climate.entity_id)

    assert mock_setup.api.set_temp.call_count == 1
    assert mock_setup.api.set_power.call_count == 1
    assert mock_setup.api.set_mode.call_count == 0
    assert state.state == HVACMode.OFF

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: climate.entity_id,
        },
        blocking=True,
    )
    state = hass.states.get(climate.entity_id)

    assert mock_setup.api.set_temp.call_count == 1
    assert mock_setup.api.set_power.call_count == 2
    assert mock_setup.api.set_mode.call_count == 1
    assert state.state == HVACMode.HEAT