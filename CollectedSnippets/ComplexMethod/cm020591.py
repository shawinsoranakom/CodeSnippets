async def test_ssdp_websocket_success_populates_mac_address_and_ssdp_location(
    hass: HomeAssistant,
) -> None:
    """Test starting a flow from ssdp for a supported device populates the mac."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=MOCK_SSDP_DATA_RENDERING_CONTROL_ST,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input="whatever"
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room (82GXARRS)"
    assert result["data"][CONF_HOST] == "10.10.12.34"
    assert result["data"][CONF_MAC] == "aa:bb:aa:aa:aa:aa"
    assert result["data"][CONF_MANUFACTURER] == "Samsung Electronics"
    assert result["data"][CONF_MODEL] == "82GXARRS"
    assert result["data"][CONF_PORT] == 8002
    assert (
        result["data"][CONF_SSDP_RENDERING_CONTROL_LOCATION]
        == "http://10.10.12.34:7676/smp_15_"
    )
    assert result["result"].unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"