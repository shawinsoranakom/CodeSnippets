async def test_user_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_airobot_client: AsyncMock,
) -> None:
    """Test user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Thermostat"
    assert result["data"] == TEST_USER_INPUT
    assert result["result"].unique_id == "T01A1B2C3"
    assert len(mock_setup_entry.mock_calls) == 1