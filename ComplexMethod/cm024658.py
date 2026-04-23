async def test_reconfigure_fails(
    hass: HomeAssistant,
    mock_amazon_devices_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    side_effect: Exception,
    error: str,
) -> None:
    """Test that the host can be reconfigured."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_amazon_devices_client.login.login_mode_interactive.side_effect = side_effect

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_CODE: TEST_CODE,
        },
    )

    assert reconfigure_result["type"] is FlowResultType.FORM
    assert reconfigure_result["step_id"] == "reconfigure"
    assert reconfigure_result["errors"] == {"base": error}

    mock_amazon_devices_client.login.login_mode_interactive.side_effect = None

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_CODE: TEST_CODE,
        },
    )

    assert reconfigure_result["type"] is FlowResultType.ABORT
    assert reconfigure_result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_LOGIN_DATA: {
            "customer_info": {"user_id": TEST_USERNAME},
            CONF_SITE: "https://www.amazon.com",
        },
    }