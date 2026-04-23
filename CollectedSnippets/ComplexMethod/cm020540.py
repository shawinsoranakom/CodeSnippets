async def test_zeroconf_add_mrp_device(hass: HomeAssistant) -> None:
    """Test add MRP device discovered by zeroconf."""
    unrelated_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.2"),
            ip_addresses=[ip_address("127.0.0.2")],
            hostname="mock_hostname",
            port=None,
            name="Kitchen",
            properties={"UniqueIdentifier": "unrelated", "Name": "Kitchen"},
            type="_mediaremotetv._tcp.local.",
        ),
    )
    assert unrelated_result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            port=None,
            name="Kitchen",
            properties={"UniqueIdentifier": "mrpid", "Name": "Kitchen"},
            type="_mediaremotetv._tcp.local.",
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["description_placeholders"] == {
        "name": "MRP Device",
        "type": "Unknown",
    }

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["description_placeholders"] == {"protocol": "MRP"}

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": 1111}
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["data"] == {
        "address": "127.0.0.1",
        "credentials": {Protocol.MRP.value: "mrp_creds"},
        "identifiers": ["mrpid"],
        "name": "MRP Device",
    }