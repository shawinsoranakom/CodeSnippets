async def test_reauth_flow_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_homevolt_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test reauthentication flow with errors and recovery."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_homevolt_client.update_info.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "wrong-password"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": expected_error}

    mock_homevolt_client.update_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "correct-password"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data == {
        CONF_HOST: "127.0.0.1",
        CONF_PASSWORD: "correct-password",
    }