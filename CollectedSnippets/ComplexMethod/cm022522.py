async def test_reconfigure(
    hass: HomeAssistant,
    mock_slide_api: AsyncMock,
    mock_config_entry: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test reconfigure flow options."""

    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "127.0.0.3",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert len(mock_setup_entry.mock_calls) == 1

    entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    assert entry
    assert entry.data[CONF_HOST] == "127.0.0.3"