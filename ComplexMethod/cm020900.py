async def test_aiodiscover_does_not_call_again_on_shorter_hostname(
    hass: HomeAssistant,
) -> None:
    """Verify longer hostnames generate a new flow but shorter ones do not.

    Some routers will truncate hostnames so we want to accept
    additional discovery where the hostname is longer and then
    reject shorter ones.
    """
    with (
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
        patch(
            "homeassistant.components.dhcp.DiscoverHosts.async_discover",
            return_value=[
                {
                    dhcp.DISCOVERY_IP_ADDRESS: "192.168.210.56",
                    dhcp.DISCOVERY_HOSTNAME: "irobot-abc",
                    dhcp.DISCOVERY_MAC_ADDRESS: "b8b7f16db533",
                },
                {
                    dhcp.DISCOVERY_IP_ADDRESS: "192.168.210.56",
                    dhcp.DISCOVERY_HOSTNAME: "irobot-abcdef",
                    dhcp.DISCOVERY_MAC_ADDRESS: "b8b7f16db533",
                },
                {
                    dhcp.DISCOVERY_IP_ADDRESS: "192.168.210.56",
                    dhcp.DISCOVERY_HOSTNAME: "irobot-abc",
                    dhcp.DISCOVERY_MAC_ADDRESS: "b8b7f16db533",
                },
            ],
        ),
    ):
        device_tracker_watcher = _make_network_watcher(
            hass,
            [
                {
                    "domain": "mock-domain",
                    "hostname": "irobot-*",
                    "macaddress": "B8B7F1*",
                }
            ],
        )
        device_tracker_watcher.async_start()
        await hass.async_block_till_done()
        device_tracker_watcher.async_stop()
        await hass.async_block_till_done()

    assert len(mock_init.mock_calls) == 2
    assert mock_init.mock_calls[0][1][0] == "mock-domain"
    assert mock_init.mock_calls[0][2]["context"] == {
        "discovery_key": DiscoveryKey(domain="dhcp", key="b8b7f16db533", version=1),
        "source": config_entries.SOURCE_DHCP,
    }
    assert mock_init.mock_calls[0][2]["data"] == DhcpServiceInfo(
        ip="192.168.210.56",
        hostname="irobot-abc",
        macaddress="b8b7f16db533",
    )
    assert mock_init.mock_calls[1][1][0] == "mock-domain"
    assert mock_init.mock_calls[1][2]["context"] == {
        "discovery_key": DiscoveryKey(domain="dhcp", key="b8b7f16db533", version=1),
        "source": config_entries.SOURCE_DHCP,
    }
    assert mock_init.mock_calls[1][2]["data"] == DhcpServiceInfo(
        ip="192.168.210.56",
        hostname="irobot-abcdef",
        macaddress="b8b7f16db533",
    )