async def test_reauth_not_successful(
    hass: HomeAssistant,
    mock_amazon_devices_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    side_effect: Exception,
    error: str,
) -> None:
    """Test starting a reauthentication flow but no connection found."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_amazon_devices_client.login.login_mode_interactive.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: "other_fake_password",
            CONF_CODE: "000000",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": error}

    mock_amazon_devices_client.login.login_mode_interactive.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: "fake_password",
            CONF_CODE: "111111",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data == {
        CONF_CODE: "111111",
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: "fake_password",
        CONF_LOGIN_DATA: {
            "customer_info": {"user_id": TEST_USERNAME},
            CONF_SITE: "https://www.amazon.com",
        },
    }