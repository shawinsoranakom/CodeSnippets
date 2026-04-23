async def test_config_flow_zeroconf_invalid(hass: HomeAssistant) -> None:
    """Test that an invalid zeroconf entry doesn't work."""
    # test with no discovery properties
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("127.0.0.1"),
        ip_addresses=[ip_address("127.0.0.1")],
        hostname="mock_hostname",
        name="mock_name",
        port=23,
        properties={},
        type="mock_type",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )  # doesn't create the entry, tries to show form but gets abort
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_forked_daapd"
    # test with forked-daapd version < 27
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("127.0.0.1"),
        ip_addresses=[ip_address("127.0.0.1")],
        hostname="mock_hostname",
        name="mock_name",
        port=23,
        properties={"mtd-version": "26.3", "Machine Name": "forked-daapd"},
        type="mock_type",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )  # doesn't create the entry, tries to show form but gets abort
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_forked_daapd"
    # test with verbose mtd-version from Firefly
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("127.0.0.1"),
        ip_addresses=[ip_address("127.0.0.1")],
        hostname="mock_hostname",
        name="mock_name",
        port=23,
        properties={"mtd-version": "0.2.4.1", "Machine Name": "firefly"},
        type="mock_type",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )  # doesn't create the entry, tries to show form but gets abort
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_forked_daapd"
    # test with svn mtd-version from Firefly
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("127.0.0.1"),
        ip_addresses=[ip_address("127.0.0.1")],
        hostname="mock_hostname",
        name="mock_name",
        port=23,
        properties={"mtd-version": "svn-1676", "Machine Name": "firefly"},
        type="mock_type",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )  # doesn't create the entry, tries to show form but gets abort
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_forked_daapd"