async def test_user_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test user flow shows form and completes successfully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PLACE_CODE: "vilnius"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Vilnius"
    assert result["data"] == {CONF_PLACE_CODE: "vilnius"}
    assert result["result"].unique_id == "vilnius"

    assert len(mock_setup_entry.mock_calls) == 1