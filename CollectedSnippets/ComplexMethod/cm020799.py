async def test_serial_flow_cannot_connect_then_recovers(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_russound_client: AsyncMock,
) -> None:
    """Test serial flow handles cannot connect and recovers."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_SERIAL},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "serial"

    mock_russound_client.connect.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_SERIAL_STEP_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "serial"
    assert result["errors"] == {"base": "cannot_connect"}

    mock_russound_client.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_SERIAL_STEP_INPUT,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MODEL
    assert result["data"] == MOCK_SERIAL_CONFIG
    assert len(mock_setup_entry.mock_calls) == 1