async def test_remove_node(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    integration,
    client,
    hass_ws_client: WebSocketGenerator,
    nortek_thermostat,
    nortek_thermostat_removed_event,
) -> None:
    """Test the remove_node websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {"success": True}

    await ws_client.send_json(
        {ID: 1, TYPE: "zwave_js/remove_node", ENTRY_ID: entry.entry_id}
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "controller.begin_exclusion",
    }

    event = Event(
        type="exclusion started",
        data={
            "source": "controller",
            "event": "exclusion started",
        },
    )
    client.driver.receive_event(event)

    msg = await ws_client.receive_json()
    assert msg["event"]["event"] == "exclusion started"

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
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "3245146787-67")},
    )
    assert device is None

    # Test unprovision parameter
    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"success": True}

    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/remove_node",
            ENTRY_ID: entry.entry_id,
            STRATEGY: ExclusionStrategy.EXCLUDE_ONLY,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "controller.begin_exclusion",
        "options": {"strategy": 0},
    }

    # Test FailedZWaveCommand is caught
    with patch(
        f"{CONTROLLER_PATCH_PREFIX}.async_begin_exclusion",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 4,
                TYPE: "zwave_js/remove_node",
                ENTRY_ID: entry.entry_id,
            }
        )
        msg = await ws_client.receive_json()

        assert not msg["success"]
        assert msg["error"]["code"] == "zwave_error"
        assert msg["error"]["message"] == "zwave_error: Z-Wave error 1 - error message"

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {ID: 5, TYPE: "zwave_js/remove_node", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED