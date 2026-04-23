async def test_flow_fails(
    hass: HomeAssistant, get_data: MockRestData, mock_setup_entry: AsyncMock
) -> None:
    """Test config flow error."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == config_entries.SOURCE_USER

    with patch(
        "homeassistant.components.rest.RestData",
        side_effect=HomeAssistantError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_RESOURCE: "https://www.home-assistant.io",
                CONF_METHOD: "GET",
                CONF_AUTH: {},
                CONF_ADVANCED: {
                    CONF_VERIFY_SSL: True,
                    CONF_TIMEOUT: 10.0,
                },
            },
        )

    assert result["errors"] == {"base": "resource_error"}

    with patch(
        "homeassistant.components.rest.RestData",
        return_value=MockRestData("test_scrape_sensor_no_data"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_RESOURCE: "https://www.home-assistant.io",
                CONF_METHOD: "GET",
                CONF_AUTH: {},
                CONF_ADVANCED: {
                    CONF_VERIFY_SSL: True,
                    CONF_TIMEOUT: 10.0,
                },
            },
        )

    assert result["errors"] == {"base": "no_data"}

    with patch(
        "homeassistant.components.rest.RestData",
        return_value=get_data,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_RESOURCE: "https://www.home-assistant.io",
                CONF_METHOD: "GET",
                CONF_AUTH: {},
                CONF_ADVANCED: {
                    CONF_VERIFY_SSL: True,
                    CONF_TIMEOUT: 10.0,
                },
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "https://www.home-assistant.io"
    assert result["options"] == {
        CONF_RESOURCE: "https://www.home-assistant.io",
        CONF_METHOD: "GET",
        CONF_AUTH: {},
        CONF_ADVANCED: {
            CONF_VERIFY_SSL: True,
            CONF_TIMEOUT: 10.0,
            CONF_ENCODING: "UTF-8",
        },
    }