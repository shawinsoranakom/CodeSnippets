async def test_set_hvac_mode(
    hass: HomeAssistant, device_climate, hvac_mode, sys_mode
) -> None:
    """Test setting hvac mode."""

    thrm_cluster = device_climate.device.device.endpoints[1].thermostat
    entity_id = find_entity_id(Platform.CLIMATE, device_climate, hass)

    state = hass.states.get(entity_id)
    assert state.state == HVACMode.OFF

    if sys_mode is not None:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: hvac_mode},
            blocking=True,
        )
        state = hass.states.get(entity_id)
        assert state.state == hvac_mode
        assert thrm_cluster.write_attributes.call_count == 1
        assert thrm_cluster.write_attributes.call_args[0][0] == {
            "system_mode": sys_mode
        }
    else:
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_HVAC_MODE,
                {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: hvac_mode},
                blocking=True,
            )
        state = hass.states.get(entity_id)
        assert thrm_cluster.write_attributes.call_count == 0
        assert state.state == HVACMode.OFF

    # turn off
    thrm_cluster.write_attributes.reset_mock()
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.OFF
    assert thrm_cluster.write_attributes.call_count == 1
    assert thrm_cluster.write_attributes.call_args[0][0] == {
        "system_mode": Thermostat.SystemMode.Off
    }