async def test_user_flow_serial_creates_entry(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_russound_client: AsyncMock,
) -> None:
    """Test serial user flow creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TYPE: TYPE_SERIAL},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "serial"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_SERIAL_STEP_INPUT,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MODEL
    assert result["data"] == MOCK_SERIAL_CONFIG
    assert len(mock_setup_entry.mock_calls) == 1
    assert result["result"].unique_id == "00:11:22:33:44:55"