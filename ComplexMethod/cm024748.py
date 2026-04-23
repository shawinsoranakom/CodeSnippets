async def test_successful_reauth(
    hass: HomeAssistant,
    mock_automower_client: Mock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test we can select a device."""

    mock_config_entry.add_to_hass(hass)

    await hass.async_block_till_done(wait_background_tasks=True)

    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Try non numeric pin
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PIN: "ABCD",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_pin"}

    # Try connection error
    mock_automower_client.connect.return_value = ResponseResult.UNKNOWN_ERROR
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PIN: "5678",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "cannot_connect"}

    # Try wrong PIN
    mock_automower_client.connect.return_value = ResponseResult.INVALID_PIN
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PIN: "5678",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_auth"}

    mock_automower_client.connect.return_value = ResponseResult.OK
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PIN: "1234",
        },
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert len(hass.config_entries.async_entries("husqvarna_automower_ble")) == 1

    assert (
        mock_config_entry.data[CONF_ADDRESS] == "00000000-0000-0000-0000-000000000003"
    )
    assert mock_config_entry.data[CONF_CLIENT_ID] == 1197489078
    assert mock_config_entry.data[CONF_PIN] == "1234"