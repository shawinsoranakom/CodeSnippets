async def test_flow_reconfigure_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_update_duckdns: AsyncMock,
    config_entry: MockConfigEntry,
    side_effect: list[Exception | bool],
    text_error: str,
) -> None:
    """Test we handle errors."""

    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_update_duckdns.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_TOKEN: NEW_TOKEN},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": text_error}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_TOKEN: NEW_TOKEN},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    assert config_entry.data[CONF_ACCESS_TOKEN] == NEW_TOKEN