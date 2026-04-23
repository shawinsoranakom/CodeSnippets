async def test_create_device(
    hass: HomeAssistant,
    knx: KNXTestKit,
    device_registry: dr.DeviceRegistry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test device creation."""
    await knx.setup_integration()
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "knx/create_device",
            "name": "Test Device",
        }
    )
    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["name"] == "Test Device"
    assert res["result"]["manufacturer"] == "KNX"
    assert res["result"]["identifiers"]
    assert res["result"]["config_entries"][0] == knx.mock_config_entry.entry_id

    device_identifier = res["result"]["identifiers"][0][1]
    assert device_registry.async_get_device({(DOMAIN, device_identifier)})
    device_id = res["result"]["id"]
    assert device_registry.async_get(device_id)