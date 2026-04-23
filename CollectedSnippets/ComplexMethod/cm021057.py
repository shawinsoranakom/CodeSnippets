async def test_device_conflict_migration(
    hass: HomeAssistant,
    mock_client: APIClient,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    issue_registry: ir.IssueRegistry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    caplog: pytest.LogCaptureFixture,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test migrating existing configuration to new hardware."""
    entity_info = [
        BinarySensorInfo(
            object_id="mybinary_sensor",
            key=1,
            name="my binary_sensor",
            is_status_binary_sensor=True,
        )
    ]
    states = [BinarySensorState(key=1, state=None)]
    user_service = []
    device = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("binary_sensor.test_my_binary_sensor")
    assert state is not None
    assert state.state == STATE_ON
    mock_config_entry = device.entry

    ent_reg_entry = entity_registry.async_get("binary_sensor.test_my_binary_sensor")
    assert ent_reg_entry
    assert ent_reg_entry.unique_id == "11:22:33:44:55:AA-binary_sensor-mybinary_sensor"
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert entries is not None
    for entry in entries:
        assert entry.unique_id.startswith("11:22:33:44:55:AA-")
    disconnect_done = hass.loop.create_future()

    async def async_disconnect(*args, **kwargs) -> None:
        if not disconnect_done.done():
            disconnect_done.set_result(None)

    mock_client.disconnect = async_disconnect
    new_device_info = DeviceInfo(
        mac_address="11:22:33:44:55:AB", name="test", model="esp32-iso-poe"
    )
    mock_client.device_info = AsyncMock(return_value=new_device_info)
    # Keep the same entity_info when reloading
    mock_client.list_entities_services = AsyncMock(return_value=(entity_info, []))
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(new_device_info, entity_info, [])
    )
    device.device_info = new_device_info
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    async with asyncio.timeout(1):
        await disconnect_done

    assert "Unexpected device found" in caplog.text
    issue_id = DEVICE_CONFLICT_ISSUE_FORMAT.format(mock_config_entry.entry_id)

    issues = await get_repairs(hass, hass_ws_client)
    assert issues
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is not None

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    data = await start_repair_fix_flow(client, DOMAIN, issue_id)

    flow_id = data["flow_id"]
    assert data["type"] == FlowResultType.MENU
    assert data["step_id"] == "init"

    data = await process_repair_fix_flow(
        client, flow_id, json={"next_step_id": "migrate"}
    )

    flow_id = data["flow_id"]
    assert data["type"] == FlowResultType.FORM
    assert data["step_id"] == "migrate"

    caplog.clear()
    data = await process_repair_fix_flow(client, flow_id)

    assert data["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert "Unexpected device found" not in caplog.text
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None

    assert mock_config_entry.unique_id == "11:22:33:44:55:ab"
    ent_reg_entry = entity_registry.async_get("binary_sensor.test_my_binary_sensor")
    assert ent_reg_entry
    assert ent_reg_entry.unique_id == "11:22:33:44:55:AB-binary_sensor-mybinary_sensor"

    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert entries is not None
    for entry in entries:
        assert entry.unique_id.startswith("11:22:33:44:55:AB-")

    dev_entry = device_registry.async_get_device(
        identifiers={}, connections={(dr.CONNECTION_NETWORK_MAC, "11:22:33:44:55:ab")}
    )
    assert dev_entry is not None

    old_dev_entry = device_registry.async_get_device(
        identifiers={}, connections={(dr.CONNECTION_NETWORK_MAC, "11:22:33:44:55:aa")}
    )
    assert old_dev_entry is None