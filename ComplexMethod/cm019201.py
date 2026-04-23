async def test_config_flow_privacy_success(
    hass: HomeAssistant, reolink_host: MagicMock, mock_setup_entry: MagicMock
) -> None:
    """Successful flow when privacy mode is turned on."""
    reolink_host.baichuan.privacy_mode.return_value = True
    reolink_host.get_host_data.side_effect = LoginPrivacyModeError("Test error")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_HOST: TEST_HOST,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "privacy"
    assert result["errors"] is None

    assert reolink_host.baichuan.set_privacy_mode.call_count == 0
    reolink_host.get_host_data.reset_mock(side_effect=True)

    with patch("homeassistant.components.reolink.config_flow.API_STARTUP_TIME", new=0):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert reolink_host.baichuan.set_privacy_mode.call_count == 1

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_NVR_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_PORT: TEST_PORT,
        CONF_USE_HTTPS: TEST_USE_HTTPS,
        CONF_SUPPORTS_PRIVACY_MODE: TEST_PRIVACY,
        CONF_BC_PORT: TEST_BC_PORT,
        CONF_BC_ONLY: False,
    }
    assert result["options"] == {
        CONF_PROTOCOL: DEFAULT_PROTOCOL,
    }
    assert result["result"].unique_id == TEST_MAC