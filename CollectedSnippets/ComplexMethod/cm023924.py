async def test_airzone_climate_set_hvac_mode(hass: HomeAssistant) -> None:
    """Test setting the HVAC mode."""

    await async_init_integration(hass)

    # Aidoos
    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: "climate.bron",
                ATTR_HVAC_MODE: HVACMode.HEAT_COOL,
            },
            blocking=True,
        )

    state = hass.states.get("climate.bron")
    assert state.state == HVACMode.HEAT_COOL

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: "climate.bron",
                ATTR_HVAC_MODE: HVACMode.OFF,
            },
            blocking=True,
        )

    state = hass.states.get("climate.bron")
    assert state.state == HVACMode.OFF

    # Groups
    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_put_group",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: "climate.group",
                ATTR_HVAC_MODE: HVACMode.DRY,
            },
            blocking=True,
        )

    state = hass.states.get("climate.group")
    assert state.state == HVACMode.DRY

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_put_group",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: "climate.group",
                ATTR_HVAC_MODE: HVACMode.OFF,
            },
            blocking=True,
        )

    state = hass.states.get("climate.group")
    assert state.state == HVACMode.OFF

    # Installations
    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_put_installation",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: "climate.house",
                ATTR_HVAC_MODE: HVACMode.DRY,
            },
            blocking=True,
        )

    state = hass.states.get("climate.house")
    assert state.state == HVACMode.DRY

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_put_installation",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: "climate.house",
                ATTR_HVAC_MODE: HVACMode.OFF,
            },
            blocking=True,
        )

    state = hass.states.get("climate.house")
    assert state.state == HVACMode.OFF

    # Zones
    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: "climate.salon",
                ATTR_HVAC_MODE: HVACMode.HEAT,
            },
            blocking=True,
        )

    state = hass.states.get("climate.salon")
    assert state.state == HVACMode.HEAT

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: "climate.salon",
                ATTR_HVAC_MODE: HVACMode.OFF,
            },
            blocking=True,
        )

    state = hass.states.get("climate.salon")
    assert state.state == HVACMode.OFF