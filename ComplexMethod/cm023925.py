async def test_airzone_climate_set_temp(hass: HomeAssistant) -> None:
    """Test setting the target temperature."""

    await async_init_integration(hass)

    # Groups
    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_put_group",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "climate.group",
                ATTR_TEMPERATURE: 20.5,
            },
            blocking=True,
        )

    state = hass.states.get("climate.group")
    assert state.attributes[ATTR_TEMPERATURE] == 20.5

    # Installations
    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_put_installation",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "climate.house",
                ATTR_HVAC_MODE: HVACMode.HEAT,
                ATTR_TEMPERATURE: 20.5,
            },
            blocking=True,
        )

    state = hass.states.get("climate.house")
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_TEMPERATURE] == 20.5

    # Zones
    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "climate.salon",
                ATTR_HVAC_MODE: HVACMode.HEAT,
                ATTR_TEMPERATURE: 20.5,
            },
            blocking=True,
        )

    state = hass.states.get("climate.salon")
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_TEMPERATURE] == 20.5

    # Aidoo Pro with Double Setpoint
    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "climate.bron_pro",
                ATTR_HVAC_MODE: HVACMode.HEAT_COOL,
                ATTR_TARGET_TEMP_HIGH: 25.0,
                ATTR_TARGET_TEMP_LOW: 20.0,
            },
            blocking=True,
        )

    state = hass.states.get("climate.bron_pro")
    assert state.state == HVACMode.HEAT_COOL
    assert state.attributes.get(ATTR_TARGET_TEMP_HIGH) == 25.0
    assert state.attributes.get(ATTR_TARGET_TEMP_LOW) == 20.0