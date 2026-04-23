async def test_interfaces_configured_from_storage_websocket_update(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """Test settings from storage can be updated via websocket api."""
    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "key": STORAGE_KEY,
        "data": {ATTR_CONFIGURED_ADAPTERS: ["eth0", "eth1", "vtun0"]},
    }
    with patch(
        "homeassistant.components.network.util.socket.socket",
        return_value=MagicMock(getsockname=Mock(return_value=[NO_LOOPBACK_IPADDR])),
    ):
        assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
        await hass.async_block_till_done()

    network_obj = hass.data[DOMAIN]
    assert network_obj.configured_adapters == ["eth0", "eth1", "vtun0"]
    ws_client = await hass_ws_client(hass)
    await ws_client.send_json({"id": 1, "type": "network"})

    response = await ws_client.receive_json()

    assert response["success"]
    assert response["result"][ATTR_CONFIGURED_ADAPTERS] == ["eth0", "eth1", "vtun0"]
    assert response["result"][ATTR_ADAPTERS] == [
        {
            "auto": False,
            "index": 1,
            "default": False,
            "enabled": True,
            "ipv4": [],
            "ipv6": [
                {
                    "address": "2001:db8::",
                    "network_prefix": 8,
                    "flowinfo": 1,
                    "scope_id": 1,
                }
            ],
            "name": "eth0",
        },
        {
            "auto": False,
            "index": 0,
            "default": False,
            "enabled": False,
            "ipv4": [{"address": "127.0.0.1", "network_prefix": 8}],
            "ipv6": [],
            "name": "lo0",
        },
        {
            "auto": True,
            "index": 2,
            "default": True,
            "enabled": True,
            "ipv4": [{"address": "192.168.1.5", "network_prefix": 23}],
            "ipv6": [],
            "name": "eth1",
        },
        {
            "auto": False,
            "index": 3,
            "default": False,
            "enabled": True,
            "ipv4": [{"address": "169.254.3.2", "network_prefix": 16}],
            "ipv6": [],
            "name": "vtun0",
        },
    ]

    await ws_client.send_json(
        {"id": 2, "type": "network/configure", "config": {ATTR_CONFIGURED_ADAPTERS: []}}
    )
    response = await ws_client.receive_json()
    assert response["result"][ATTR_CONFIGURED_ADAPTERS] == []

    await ws_client.send_json({"id": 3, "type": "network"})
    response = await ws_client.receive_json()
    assert response["result"][ATTR_CONFIGURED_ADAPTERS] == []
    assert response["result"][ATTR_ADAPTERS] == [
        {
            "auto": False,
            "index": 1,
            "default": False,
            "enabled": False,
            "ipv4": [],
            "ipv6": [
                {
                    "address": "2001:db8::",
                    "network_prefix": 8,
                    "flowinfo": 1,
                    "scope_id": 1,
                }
            ],
            "name": "eth0",
        },
        {
            "auto": False,
            "index": 0,
            "default": False,
            "enabled": False,
            "ipv4": [{"address": "127.0.0.1", "network_prefix": 8}],
            "ipv6": [],
            "name": "lo0",
        },
        {
            "auto": True,
            "index": 2,
            "default": True,
            "enabled": True,
            "ipv4": [{"address": "192.168.1.5", "network_prefix": 23}],
            "ipv6": [],
            "name": "eth1",
        },
        {
            "auto": False,
            "index": 3,
            "default": False,
            "enabled": False,
            "ipv4": [{"address": "169.254.3.2", "network_prefix": 16}],
            "ipv6": [],
            "name": "vtun0",
        },
    ]