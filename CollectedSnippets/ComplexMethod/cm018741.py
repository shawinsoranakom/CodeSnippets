async def test_full_user_flow(
    hass: HomeAssistant, mock_palazzetti_client: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.1"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Stove"
    assert result["data"] == {CONF_HOST: "192.168.1.1"}
    assert result["result"].unique_id == "11:22:33:44:55:66"
    assert len(mock_palazzetti_client.connect.mock_calls) > 0