async def test_reconfigure_flow(
    hass: HomeAssistant,
    mock_mealie_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure flow."""
    await setup_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "http://test:9090",
            CONF_API_TOKEN: "token2",
            CONF_VERIFY_SSL: False,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_API_TOKEN] == "token2"
    assert mock_config_entry.data[CONF_HOST] == "http://test:9090"
    assert mock_config_entry.data[CONF_VERIFY_SSL] is False