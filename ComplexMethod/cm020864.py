async def test_full_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_homevolt_client: MagicMock
) -> None:
    """Test a complete successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    user_input = {
        CONF_HOST: "192.168.1.100",
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Homevolt"
    assert result["data"] == {CONF_HOST: "192.168.1.100", CONF_PASSWORD: None}
    assert result["result"].unique_id == "40580137858664"
    assert len(mock_setup_entry.mock_calls) == 1