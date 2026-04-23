async def test_setup_flow(
    hass: HomeAssistant,
    mock_satel: AsyncMock,
    mock_setup_entry: AsyncMock,
    user_input_connection: dict[str, Any],
    user_input_code: dict[str, Any],
    entry_data: dict[str, Any],
    entry_options: dict[str, Any],
) -> None:
    """Test the setup flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input_connection,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "code"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input_code,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_CONFIG_DATA[CONF_HOST]
    assert result["data"] == entry_data
    assert result["options"] == entry_options

    assert len(mock_setup_entry.mock_calls) == 1