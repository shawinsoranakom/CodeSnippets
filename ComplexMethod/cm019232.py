async def test_step_user(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_immich: Mock
) -> None:
    """Test a user initiated config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "user"
    assert result["data"] == MOCK_CONFIG_ENTRY_DATA
    assert result["result"].unique_id == "e7ef5713-9dab-4bd4-b899-715b0ca4379e"
    assert len(mock_setup_entry.mock_calls) == 1