async def test_add_device_api(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test adding an Insteon device."""

    ws_client, devices, _, _ = await async_mock_setup(hass, hass_ws_client)
    with patch.object(insteon.api.device, "devices", devices):
        await ws_client.send_json({ID: 2, TYPE: "insteon/device/add", MULTIPLE: True})

        await asyncio.sleep(0.01)
        assert devices.async_add_device_called_with.get("address") is None
        assert devices.async_add_device_called_with["multiple"] is True

        msg = await ws_client.receive_json()
        assert msg["event"]["type"] == "device_added"
        assert msg["event"]["address"] == "aa.bb.cc"

        msg = await ws_client.receive_json()
        assert msg["event"]["type"] == "device_added"
        assert msg["event"]["address"] == "bb.cc.dd"

        publish_topic(
            DEVICE_LIST_CHANGED,
            address=None,
            action=DeviceAction.COMPLETED,
        )
        msg = await ws_client.receive_json()
        assert msg["event"]["type"] == "linking_stopped"