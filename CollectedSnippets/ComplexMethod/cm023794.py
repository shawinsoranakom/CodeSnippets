async def test_zeroconf_discovery(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_charger: MagicMock
) -> None:
    """Test zeroconf discovery."""
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.123"),
        ip_addresses=[ip_address("192.168.1.123")],
        hostname="openevse-deadbeeffeed.local.",
        name="openevse-deadbeeffeed._openevse._tcp.local.",
        port=80,
        properties={"id": "deadbeeffeed", "type": "openevse"},
        type="_openevse._tcp.local.",
    )

    # Trigger the zeroconf step
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    # Should present a confirmation form
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert result["description_placeholders"] == {
        "name": "OpenEVSE openevse-deadbeeffeed"
    }

    # Confirm the discovery
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    # Should create the entry
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OpenEVSE openevse-deadbeeffeed"
    assert result["data"] == {CONF_HOST: "192.168.1.123"}
    assert result["result"].unique_id == "deadbeeffeed"