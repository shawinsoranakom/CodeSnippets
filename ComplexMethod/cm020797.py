async def test_tcp_flow_cannot_connect_then_recovers(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_russound_client: AsyncMock
) -> None:
    """Test TCP flow handles cannot connect and recovers."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_TCP},
    )
    assert result["step_id"] == "tcp"

    mock_russound_client.connect.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_TCP_STEP_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "tcp"
    assert result["errors"] == {"base": "cannot_connect"}

    mock_russound_client.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_TCP_STEP_INPUT,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == MOCK_TCP_CONFIG
    assert len(mock_setup_entry.mock_calls) == 1