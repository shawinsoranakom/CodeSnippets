async def test_dhcp_rediscover(
    hass: HomeAssistant,
    entry_domain: str,
    entry_discovery_keys: dict[str, tuple[DiscoveryKey, ...]],
    entry_source: str,
) -> None:
    """Test we reinitiate flows when an ignored config entry is removed."""

    entry = MockConfigEntry(
        domain=entry_domain,
        discovery_keys=entry_discovery_keys,
        unique_id="mock-unique-id",
        state=config_entries.ConfigEntryState.LOADED,
        source=entry_source,
    )
    entry.add_to_hass(hass)

    address_data = {}
    integration_matchers = dhcp.async_index_integration_matchers(
        [{"domain": "mock-domain", "hostname": "connect", "macaddress": "B8B7F1*"}]
    )
    packet = Ether(RAW_DHCP_REQUEST)

    async_handle_dhcp_packet = await _async_get_handle_dhcp_packet(
        hass, integration_matchers, address_data
    )
    rediscovery_watcher = dhcp.RediscoveryWatcher(
        hass, DHCPData(integration_matchers, set(), address_data)
    )
    rediscovery_watcher.async_start()
    with patch.object(hass.config_entries.flow, "async_init") as mock_init:
        await async_handle_dhcp_packet(packet)
        # Ensure no change is ignored
        await async_handle_dhcp_packet(packet)

    # Assert the cached MAC address is hexstring without :
    assert address_data == {
        "b8b7f16db533": {"hostname": "connect", "ip": "192.168.210.56"}
    }

    expected_context = {
        "discovery_key": DiscoveryKey(domain="dhcp", key="b8b7f16db533", version=1),
        "source": config_entries.SOURCE_DHCP,
    }
    assert len(mock_init.mock_calls) == 1
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == expected_context
    assert mock_init.mock_calls[0][2]["data"] == DhcpServiceInfo(
        ip="192.168.210.56",
        hostname="connect",
        macaddress="b8b7f16db533",
    )

    with patch.object(hass.config_entries.flow, "async_init") as mock_init:
        await hass.config_entries.async_remove(entry.entry_id)
        await hass.async_block_till_done()

        assert len(mock_init.mock_calls) == 1
        assert mock_init.mock_calls[0][1][0] == "mock-domain"
        assert mock_init.mock_calls[0][2]["context"] == expected_context