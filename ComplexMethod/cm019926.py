async def test_auth_fail(
    gogogate2api_mock, async_setup_entry_mock, hass: HomeAssistant
) -> None:
    """Test authorization failures."""
    api: GogoGate2Api = MagicMock(spec=GogoGate2Api)
    gogogate2api_mock.return_value = api

    api.reset_mock()
    api.async_info.side_effect = ApiError(
        GogoGate2ApiErrorCode.CREDENTIALS_INCORRECT, "blah"
    )
    result = await hass.config_entries.flow.async_init(
        "gogogate2", context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE: DEVICE_TYPE_GOGOGATE2,
            CONF_IP_ADDRESS: "127.0.0.2",
            CONF_USERNAME: "user0",
            CONF_PASSWORD: "password0",
        },
    )
    assert result
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        "base": "invalid_auth",
    }

    api.reset_mock()
    api.async_info.side_effect = Exception("Generic connection error.")
    result = await hass.config_entries.flow.async_init(
        "gogogate2", context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE: DEVICE_TYPE_GOGOGATE2,
            CONF_IP_ADDRESS: "127.0.0.2",
            CONF_USERNAME: "user0",
            CONF_PASSWORD: "password0",
        },
    )
    assert result
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    api.reset_mock()
    api.async_info.side_effect = ApiError(0, "blah")
    result = await hass.config_entries.flow.async_init(
        "gogogate2", context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE: DEVICE_TYPE_GOGOGATE2,
            CONF_IP_ADDRESS: "127.0.0.2",
            CONF_USERNAME: "user0",
            CONF_PASSWORD: "password0",
        },
    )
    assert result
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}