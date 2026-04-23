async def test_reconfigure_fail_with_error(
    hass: HomeAssistant,
    mock_lunatone_info: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test reconfigure flow with an error."""
    url = URL.build(scheme="http", host="10.0.0.100").human_repr()[:-1]

    mock_lunatone_info.async_update.side_effect = exception

    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: url}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}

    mock_lunatone_info.async_update.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: url}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {CONF_URL: url}