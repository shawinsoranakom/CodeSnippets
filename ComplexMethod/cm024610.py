async def test_discovered_via_zeroconf(
    hass: HomeAssistant, service: MagicMock, snapshot: SnapshotAssertion
) -> None:
    """Test we can setup from zeroconf."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.5"),
            ip_addresses=[ip_address("192.168.1.5")],
            port=5000,
            hostname="mydsm.local.",
            type="_http._tcp.local.",
            name="mydsm._http._tcp.local.",
            properties={
                "mac_address": "00:11:32:XX:XX:99|00:11:22:33:44:55",  # MAC address, but SSDP does not have `-`
            },
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.synology_dsm.config_flow.SynologyDSM",
        return_value=service,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL
    assert result["title"] == "mydsm"
    assert result["data"] == snapshot