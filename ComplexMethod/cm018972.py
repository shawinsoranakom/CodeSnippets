async def test_user_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test the full manual user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCK_HOSTNAME,
        },
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "SLZB-06p7"
    assert result2["data"] == {
        CONF_HOST: MOCK_HOSTNAME,
    }
    assert result2["context"]["unique_id"] == "aa:bb:cc:dd:ee:ff"
    assert len(mock_setup_entry.mock_calls) == 1