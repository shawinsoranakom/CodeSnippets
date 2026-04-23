async def test_user_flow_creates_entry(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_kiosker_api: MagicMock,
) -> None:
    """Test the full user config flow creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.100",
            CONF_API_TOKEN: "test-token",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Kiosker A98BE1CE"
    assert result2["data"] == {
        CONF_HOST: "192.168.1.100",
        CONF_API_TOKEN: "test-token",
        CONF_SSL: False,
        CONF_VERIFY_SSL: False,
    }
    assert result2["result"].unique_id == "A98BE1CE-5FE7-4A8D-B2C3-123456789ABC"
    assert len(mock_setup_entry.mock_calls) == 1