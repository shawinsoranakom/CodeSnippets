async def test_reconfigure(
    hass: HomeAssistant,
    mock_homewizardenergy: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfiguration."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {}

    # original entry
    assert mock_config_entry.data[CONF_IP_ADDRESS] == "127.0.0.1"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_IP_ADDRESS: "1.0.0.127",
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # changed entry
    assert mock_config_entry.data[CONF_IP_ADDRESS] == "1.0.0.127"