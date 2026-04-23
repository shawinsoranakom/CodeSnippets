async def test_notify_on_aldb_loading(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, aldb_data
) -> None:
    """Test tracking changes to ALDB status across all devices."""
    ws_client, devices = await _setup(hass, hass_ws_client, aldb_data)

    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json_auto_id({TYPE: "insteon/aldb/notify_all"})
        msg = await ws_client.receive_json()
        assert msg["success"]

        await asyncio.sleep(0.1)
        msg = await ws_client.receive_json()
        assert msg["event"]["type"] == "status"
        assert not msg["event"]["is_loading"]

        device = devices["333333"]
        device.aldb._update_status(ALDBStatus.LOADING)
        await asyncio.sleep(0.1)
        msg = await ws_client.receive_json()
        assert msg["event"]["type"] == "status"
        assert msg["event"]["is_loading"]

        device.aldb._update_status(ALDBStatus.LOADED)
        await asyncio.sleep(0.1)
        msg = await ws_client.receive_json()
        assert msg["event"]["type"] == "status"
        assert not msg["event"]["is_loading"]

        await ws_client.client.session.close()

        # Allow lingering tasks to complete
        await asyncio.sleep(0.1)