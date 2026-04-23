async def test_migrate_unique_id(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    client: MagicMock,
    multisensor_6: Node,
) -> None:
    """Test the migrate unique id flow."""
    node = multisensor_6
    old_unique_id = "123456789"
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={
            "url": "ws://test.org",
        },
        unique_id=old_unique_id,
    )
    config_entry.add_to_hass(hass)

    # Remove the node from the current controller's known nodes.
    client.driver.controller.nodes.pop(node.node_id)

    # Create a device entry for the node connected to the old controller.
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, f"{old_unique_id}-{node.node_id}")},
        name="Node connected to old controller",
    )
    assert device_entry.name == "Node connected to old controller"

    await hass.config_entries.async_setup(config_entry.entry_id)

    assert CONF_KEEP_OLD_DEVICES in config_entry.data
    assert config_entry.data[CONF_KEEP_OLD_DEVICES] is True
    stored_devices = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    assert len(stored_devices) == 2
    assert device_entry.id in {device.id for device in stored_devices}

    await async_process_repairs_platforms(hass)
    ws_client = await hass_ws_client(hass)
    http_client = await hass_client()

    # Assert the issue is present
    await ws_client.send_json_auto_id({"type": "repairs/list_issues"})
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["issues"]) == 1
    issue = msg["result"]["issues"][0]
    issue_id = issue["issue_id"]
    assert issue_id == f"migrate_unique_id.{config_entry.entry_id}"

    data = await start_repair_fix_flow(http_client, DOMAIN, issue_id)

    flow_id = data["flow_id"]
    assert data["step_id"] == "confirm"
    assert data["description_placeholders"] == {
        "config_entry_title": "Z-Wave JS",
        "controller_model": "ZW090",
        "new_unique_id": "0xc16d02a3",
        "old_unique_id": "0x075bcd15",
    }

    # Apply fix
    data = await process_repair_fix_flow(http_client, flow_id)
    await hass.async_block_till_done()

    stored_devices = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    assert len(stored_devices) == 1
    assert device_entry.id not in {device.id for device in stored_devices}

    assert data["type"] == "create_entry"
    assert config_entry.unique_id == "3245146787"

    await ws_client.send_json_auto_id({"type": "repairs/list_issues"})
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["issues"]) == 0