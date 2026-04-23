async def test_discovery_initiation(hass: HomeAssistant) -> None:
    """Test discovery importing works."""
    service_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.43.183"),
        ip_addresses=[ip_address("192.168.43.183")],
        hostname="test.local.",
        name="mock_name",
        port=6053,
        properties={
            "mac": "1122334455aa",
            "friendly_name": "The Test",
        },
        type="mock_type",
    )
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=service_info
    )
    assert get_flow_context(hass, flow) == {
        "source": config_entries.SOURCE_ZEROCONF,
        "title_placeholders": {"name": "The Test (test)"},
        "unique_id": "11:22:33:44:55:aa",
    }

    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test"
    assert result["data"][CONF_HOST] == "192.168.43.183"
    assert result["data"][CONF_PORT] == 6053

    assert result["result"]
    assert result["result"].unique_id == "11:22:33:44:55:aa"