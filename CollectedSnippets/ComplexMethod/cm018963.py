async def test_reconfigure_connection_failed(
    hass: HomeAssistant,
    mock_satel: AsyncMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    error: str,
) -> None:
    """Failure path for the reconfigure flow."""

    mock_satel.connect.side_effect = exception

    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": error}

    mock_satel.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    assert mock_config_entry.data == {
        CONF_HOST: "1.2.3.4",
        CONF_PORT: 1234,
        CONF_ENCRYPTION_KEY: None,
    }