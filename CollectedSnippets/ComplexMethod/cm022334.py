async def test_bsb003_bridge_discovery(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test a bridge being discovered."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        data={"host": "192.168.1.217", "api_version": 2, "api_key": "abc"},
        unique_id="bsb002_00000",
    )
    entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(const.DOMAIN, "bsb002_00000")},
        connections={(dr.CONNECTION_NETWORK_MAC, "AA:BB:CC:DD:EE:FF")},
    )
    create_mock_api_discovery(
        aioclient_mock,
        [("192.168.1.217", "bsb002_00000"), ("192.168.1.218", "bsb003_00000")],
    )
    disc_bridge = get_discovered_bridge(
        bridge_id="bsb003_00000", host="192.168.1.218", supports_v2=True
    )

    with (
        patch(
            "homeassistant.components.hue.config_flow.discover_bridge",
            return_value=disc_bridge,
        ),
        patch(
            "homeassistant.components.hue.config_flow.HueBridgeV2",
            autospec=True,
        ) as mock_bridge,
    ):
        mock_bridge.return_value.fetch_full_state.return_value = {}
        result = await hass.config_entries.flow.async_init(
            const.DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("192.168.1.218"),
                ip_addresses=[ip_address("192.168.1.218")],
                port=443,
                hostname="Philips-hue.local",
                type="_hue._tcp.local.",
                name="Philips Hue - ABCABC._hue._tcp.local.",
                properties={
                    "bridgeid": "bsb003_00000",
                    "modelid": "BSB003",
                },
            ),
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "migrated_bridge"

    migrated_device = device_registry.async_get(device.id)

    assert migrated_device is not None
    assert len(migrated_device.identifiers) == 1
    assert list(migrated_device.identifiers)[0] == (const.DOMAIN, "bsb003_00000")
    # The tests don't add new connection, but that will happen
    # outside of the config flow
    assert len(migrated_device.connections) == 0
    assert entry.data["host"] == "192.168.1.218"