async def test_airzone_climate_turn_on_off(hass: HomeAssistant) -> None:
    """Test turning on/off."""

    await async_init_integration(hass)

    # Aidoos
    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: "climate.bron",
            },
            blocking=True,
        )

    state = hass.states.get("climate.bron")
    assert state.state == HVACMode.HEAT

    # Groups
    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_put_group",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: "climate.group",
            },
            blocking=True,
        )

    state = hass.states.get("climate.group")
    assert state.state == HVACMode.COOL

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_put_group",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_OFF,
            {
                ATTR_ENTITY_ID: "climate.group",
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
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: "climate.house",
            },
            blocking=True,
        )

    state = hass.states.get("climate.house")
    assert state.state == HVACMode.COOL

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_put_installation",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_OFF,
            {
                ATTR_ENTITY_ID: "climate.house",
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
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: "climate.dormitorio",
            },
            blocking=True,
        )

    state = hass.states.get("climate.dormitorio")
    assert state.state == HVACMode.COOL

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_TURN_OFF,
            {
                ATTR_ENTITY_ID: "climate.salon",
            },
            blocking=True,
        )

    state = hass.states.get("climate.salon")
    assert state.state == HVACMode.OFF