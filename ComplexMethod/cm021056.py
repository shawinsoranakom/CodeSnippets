async def test_device_conflict_manual(
    hass: HomeAssistant,
    mock_client: APIClient,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    mock_config_entry: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test guided manual conflict resolution."""
    disconnect_done = hass.loop.create_future()

    async def async_disconnect(*args, **kwargs) -> None:
        disconnect_done.set_result(None)

    mock_client.disconnect = async_disconnect
    device_info = DeviceInfo(
        mac_address="1122334455ab", name="test", model="esp32-iso-poe"
    )
    mock_client.device_info = AsyncMock(return_value=device_info)
    mock_client.list_entities_services = AsyncMock(return_value=([], []))
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(device_info, [], [])
    )
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
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
        client, flow_id, json={"next_step_id": "manual"}
    )

    flow_id = data["flow_id"]
    assert data["type"] == FlowResultType.FORM
    assert data["step_id"] == "manual"

    device_info = DeviceInfo(
        mac_address="11:22:33:44:55:aa", name="test", model="esp32-iso-poe"
    )
    mock_client.device_info = AsyncMock(return_value=device_info)
    mock_client.list_entities_services = AsyncMock(return_value=([], []))
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(device_info, [], [])
    )
    caplog.clear()
    data = await process_repair_fix_flow(client, flow_id)

    assert data["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert "Unexpected device found" not in caplog.text
    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None