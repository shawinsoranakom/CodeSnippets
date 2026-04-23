async def test_remove_failed_node(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    nortek_thermostat,
    integration,
    client,
    hass_ws_client: WebSocketGenerator,
    nortek_thermostat_removed_event,
    nortek_thermostat_added_event,
) -> None:
    """Test the remove_failed_node websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    device = get_device(hass, nortek_thermostat)

    client.async_send_command.return_value = {"success": True}

    # Test FailedZWaveCommand is caught
    with patch(
        f"{CONTROLLER_PATCH_PREFIX}.async_remove_failed_node",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 1,
                TYPE: "zwave_js/remove_failed_node",
                DEVICE_ID: device.id,
            }
        )
        msg = await ws_client.receive_json()

        assert not msg["success"]
        assert msg["error"]["code"] == "zwave_error"
        assert msg["error"]["message"] == "zwave_error: Z-Wave error 1 - error message"

    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/remove_failed_node",
            DEVICE_ID: device.id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    # Create device registry entry for mock node
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "3245146787-67")},
        name="Node 67",
    )

    # Fire node removed event
    client.driver.receive_event(nortek_thermostat_removed_event)
    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "node removed"

    # Verify device was removed from device registry
    assert (
        device_registry.async_get_device(
            identifiers={(DOMAIN, "3245146787-67")},
        )
        is None
    )

    # Re-add node so we can test config entry not loaded
    client.driver.receive_event(nortek_thermostat_added_event)

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/remove_failed_node",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED