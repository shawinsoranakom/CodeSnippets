async def test_user_flow_minimum_fields_in_zone(hass: HomeAssistant) -> None:
    """Test user config flow with minimum fields."""
    assert await async_setup_component(
        hass,
        "zone",
        {
            "zone": {
                CONF_NAME: "Home",
                CONF_LATITUDE: hass.config.latitude,
                CONF_LONGITUDE: hass.config.longitude,
                CONF_RADIUS: 100,
            }
        },
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=_get_config_schema(hass, SOURCE_USER, MIN_CONFIG)(MIN_CONFIG),
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{DEFAULT_NAME} - Home"
    assert result["data"][CONF_NAME] == f"{DEFAULT_NAME} - Home"
    assert result["data"][CONF_API_KEY] == API_KEY
    assert result["data"][CONF_LOCATION][CONF_LATITUDE] == hass.config.latitude
    assert result["data"][CONF_LOCATION][CONF_LONGITUDE] == hass.config.longitude