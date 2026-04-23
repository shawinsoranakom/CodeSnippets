async def test_zeroconf_pair_additionally_found_protocols(
    hass: HomeAssistant, mock_scan: AsyncMock
) -> None:
    """Test discovered protocols are merged to original flow."""
    mock_scan.result = [
        create_conf(IPv4Address("127.0.0.1"), "Device", airplay_service())
    ]

    # Find device with AirPlay service and set up flow for it
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            port=None,
            type="_airplay._tcp.local.",
            name="Kitchen",
            properties={"deviceid": "airplayid"},
        ),
    )
    assert result["type"] is FlowResultType.FORM
    await hass.async_block_till_done()

    mock_scan.result = [
        create_conf(
            IPv4Address("127.0.0.1"), "Device", raop_service(), airplay_service()
        )
    ]

    # Find the same device again, but now also with RAOP service. The first flow should
    # be updated with the RAOP service.
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=RAOP_SERVICE,
    )
    await hass.async_block_till_done()

    mock_scan.result = [
        create_conf(
            IPv4Address("127.0.0.1"),
            "Device",
            raop_service(),
            mrp_service(),
            airplay_service(),
        )
    ]

    # Find the same device again, but now also with MRP service. The first flow should
    # be updated with the MRP service.
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            port=None,
            type="_mediaremotetv._tcp.local.",
            name="Kitchen",
            properties={"UniqueIdentifier": "mrpid", "Name": "Kitchen"},
        ),
    )
    await hass.async_block_till_done()

    # Verify that all protocols are paired
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "pair_no_pin"
    assert result2["description_placeholders"] == {"pin": ANY, "protocol": "RAOP"}

    # Verify that all protocols are paired
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "pair_with_pin"
    assert result3["description_placeholders"] == {"protocol": "MRP"}

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"pin": 1234},
    )
    assert result4["type"] is FlowResultType.FORM
    assert result4["step_id"] == "pair_with_pin"
    assert result4["description_placeholders"] == {"protocol": "AirPlay"}

    result5 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"pin": 1234},
    )
    assert result5["type"] is FlowResultType.CREATE_ENTRY