async def test_climate_hvac_action_running_state(
    hass: HomeAssistant, device_climate_sinope
) -> None:
    """Test hvac action via running state."""

    thrm_cluster = device_climate_sinope.device.device.endpoints[1].thermostat
    entity_id = find_entity_id(Platform.CLIMATE, device_climate_sinope, hass)
    sensor_entity_id = find_entity_id(
        Platform.SENSOR, device_climate_sinope, hass, "hvac"
    )

    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF
    hvac_sensor_state = hass.states.get(sensor_entity_id)
    assert hvac_sensor_state.state == HVACAction.OFF

    await send_attributes_report(
        hass, thrm_cluster, {0x001E: Thermostat.RunningMode.Off}
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF
    hvac_sensor_state = hass.states.get(sensor_entity_id)
    assert hvac_sensor_state.state == HVACAction.OFF

    await send_attributes_report(
        hass, thrm_cluster, {0x001C: Thermostat.SystemMode.Auto}
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    hvac_sensor_state = hass.states.get(sensor_entity_id)
    assert hvac_sensor_state.state == HVACAction.IDLE

    await send_attributes_report(
        hass, thrm_cluster, {0x001E: Thermostat.RunningMode.Cool}
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.COOLING
    hvac_sensor_state = hass.states.get(sensor_entity_id)
    assert hvac_sensor_state.state == HVACAction.COOLING

    await send_attributes_report(
        hass, thrm_cluster, {0x001E: Thermostat.RunningMode.Heat}
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.HEATING
    hvac_sensor_state = hass.states.get(sensor_entity_id)
    assert hvac_sensor_state.state == HVACAction.HEATING

    await send_attributes_report(
        hass, thrm_cluster, {0x001E: Thermostat.RunningMode.Off}
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    hvac_sensor_state = hass.states.get(sensor_entity_id)
    assert hvac_sensor_state.state == HVACAction.IDLE

    await send_attributes_report(
        hass, thrm_cluster, {0x0029: Thermostat.RunningState.Fan_State_On}
    )
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.FAN
    hvac_sensor_state = hass.states.get(sensor_entity_id)
    assert hvac_sensor_state.state == HVACAction.FAN