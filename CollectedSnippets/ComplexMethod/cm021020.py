async def test_user_flow_create_entry(hass: HomeAssistant) -> None:
    """Test the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "WiiM Pro"
    assert result["data"] == {CONF_HOST: "192.168.1.100"}
    assert result["result"].unique_id == "uuid:test-udn-1234"