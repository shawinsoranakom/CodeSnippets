async def test_full_form(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_poolsense_client: AsyncMock
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@test.com", CONF_PASSWORD: "test"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@test.com"
    assert result["data"] == {
        CONF_EMAIL: "test@test.com",
        CONF_PASSWORD: "test",
    }
    assert result["result"].unique_id == "test@test.com"

    assert len(mock_setup_entry.mock_calls) == 1