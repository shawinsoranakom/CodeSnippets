async def test_reauth_config_flow_auth_error(
    hass: HomeAssistant, mock_device: AsyncMock, mock_integration: MockConfigEntry
) -> None:
    """Test reauth config flow when connect fails."""
    mock_device.connect.side_effect = JvcProjectorAuthError

    result = await mock_integration.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_auth"}

    # Finish flow with success

    mock_device.connect.side_effect = None

    result = await mock_integration.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: MOCK_PASSWORD}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert mock_integration.data[CONF_HOST] == MOCK_HOST
    assert mock_integration.data[CONF_PORT] == MOCK_PORT
    assert mock_integration.data[CONF_PASSWORD] == MOCK_PASSWORD