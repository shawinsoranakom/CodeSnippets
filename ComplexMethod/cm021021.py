async def test_zeroconf_flow(hass: HomeAssistant) -> None:
    """Test the zeroconf discovery flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert result["description_placeholders"] == {"name": "WiiM Pro"}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "WiiM Pro"
    assert result["data"] == {CONF_HOST: "192.168.1.100"}
    assert result["result"].unique_id == "uuid:test-udn-1234"