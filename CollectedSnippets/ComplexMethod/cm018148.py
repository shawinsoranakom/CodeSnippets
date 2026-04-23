async def test_full_flow(hass: HomeAssistant) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.123"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_NAME
    assert result["data"] == {
        CONF_HOST: "192.168.0.123",
        CONF_ID: "00000000-0000-0000-0000-000000000000",
        CONF_NAME: TEST_NAME,
        CONF_MODEL: TEST_MODEL,
    }
    assert result["result"].unique_id == TEST_MAC