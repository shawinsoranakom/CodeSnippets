async def test_reauth_flow_errors_with_recovery(
    hass: HomeAssistant,
    mock_teltasync_client: MagicMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test reauth flow error handling with successful recovery."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    mock_teltasync_client.get_device_info.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "bad_password",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}
    assert result["step_id"] == "reauth_confirm"

    mock_teltasync_client.get_device_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "new_password",
        },
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_USERNAME] == "admin"
    assert mock_config_entry.data[CONF_PASSWORD] == "new_password"
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.1"