async def test_device_config_file_changed_ignore_step(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    client: Client,
    multisensor_6_state: NodeDataType,
    integration: MockConfigEntry,
) -> None:
    """Test the device_config_file_changed issue ignore step."""
    node = await _trigger_repair_issue(hass, client, multisensor_6_state)

    client.async_send_command_no_wait.reset_mock()

    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, node)}
    )
    assert device
    issue_id = f"device_config_file_changed.{device.id}"

    await async_process_repairs_platforms(hass)
    ws_client = await hass_ws_client(hass)
    http_client = await hass_client()

    # Assert the issue is present
    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["issues"]) == 1
    issue = msg["result"]["issues"][0]
    assert issue["issue_id"] == issue_id
    assert issue["translation_placeholders"] == {"device_name": device.name}

    data = await start_repair_fix_flow(http_client, DOMAIN, issue_id)

    flow_id = data["flow_id"]
    assert data["step_id"] == "init"
    assert data["description_placeholders"] == {"device_name": device.name}

    # Show menu
    data = await process_repair_fix_flow(http_client, flow_id)

    assert data["type"] == "menu"

    # Ignore the issue
    data = await process_repair_fix_flow(
        http_client, flow_id, json={"next_step_id": "ignore"}
    )

    assert data["type"] == "abort"
    assert data["reason"] == "issue_ignored"
    assert data["description_placeholders"] == {"device_name": device.name}

    await hass.async_block_till_done()

    assert len(client.async_send_command_no_wait.call_args_list) == 0

    # Assert the issue still exists but is ignored
    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["issues"]) == 1
    assert msg["result"]["issues"][0].get("dismissed_version") is not None