async def test_rtsp_writable_fix_when_not_setup(
    hass: HomeAssistant,
    ufp: MockUFPFixture,
    doorbell: Camera,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test RTSP disabled warning if the integration is no longer set up."""

    for channel in doorbell.channels:
        channel.is_rtsp_enabled = False

    await init_entry(hass, ufp, [doorbell])
    await async_process_repairs_platforms(hass)
    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    new_doorbell = deepcopy(doorbell)
    new_doorbell.channels[0].is_rtsp_enabled = True

    ufp.api.get_camera = AsyncMock(side_effect=[doorbell, new_doorbell])
    ufp.api.create_camera_rtsps_streams = AsyncMock(return_value=None)
    issue_id = f"rtsp_disabled_{doorbell.id}"

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    assert msg["success"]
    assert len(msg["result"]["issues"]) > 0
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == issue_id:
            issue = i
    assert issue is not None

    # Unload the integration to ensure the fix flow still works
    # if the integration is no longer set up
    await hass.config_entries.async_unload(ufp.entry.entry_id)
    await hass.async_block_till_done()

    data = await start_repair_fix_flow(client, DOMAIN, issue_id)

    flow_id = data["flow_id"]
    assert data["step_id"] == "start"

    data = await process_repair_fix_flow(client, flow_id)

    assert data["type"] == "create_entry"

    ufp.api.create_camera_rtsps_streams.assert_called_with(doorbell.id, "high")