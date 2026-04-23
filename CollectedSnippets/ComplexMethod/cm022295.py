async def test_user_flow_success(
    hass: HomeAssistant,
    mock_duco_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test a successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "SILENT_CONNECT"
    assert result["data"] == USER_INPUT
    assert result["result"].unique_id == TEST_MAC