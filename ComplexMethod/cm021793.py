async def test_user_tv_pairing_no_apps(hass: HomeAssistant) -> None:
    """Test pairing config flow when access token not provided for tv during user entry and no apps configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_TV_CONFIG_NO_TOKEN
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pair_tv"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_PIN_CONFIG
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pairing_complete"

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"][CONF_NAME] == NAME
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_DEVICE_CLASS] == MediaPlayerDeviceClass.TV
    assert CONF_APPS not in result["data"]