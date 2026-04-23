async def test_user_flow_all_fields(hass: HomeAssistant) -> None:
    """Test user config flow with all fields."""
    # test form shows
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_VALID_TV_CONFIG
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"][CONF_NAME] == NAME
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_DEVICE_CLASS] == MediaPlayerDeviceClass.TV
    assert result["data"][CONF_ACCESS_TOKEN] == ACCESS_TOKEN
    assert CONF_APPS not in result["data"]