async def test_websocket_no_mac(hass: HomeAssistant, mac_address: Mock) -> None:
    """Test for send key with autodetection of protocol."""
    mac_address.return_value = "gg:ee:tt:mm:aa:cc"
    with (
        patch(
            "homeassistant.components.samsungtv.bridge.Remote",
            side_effect=OSError("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVWSAsyncRemote"
        ) as remote_websocket,
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVAsyncRest",
        ) as rest_api_class,
    ):
        remote = Mock(SamsungTVWSAsyncRemote)
        remote.__aenter__ = AsyncMock(return_value=remote)
        remote.__aexit__ = AsyncMock(return_value=False)
        rest_api_class.return_value.rest_device_info = AsyncMock(
            return_value={
                "id": "uuid:be9554b9-c9fb-41f4-8920-22da015376a4",
                "device": {
                    "modelName": "82GXARRS",
                    "networkType": "lan",
                    "udn": "uuid:be9554b9-c9fb-41f4-8920-22da015376a4",
                    "name": "[TV] Living Room",
                    "type": "Samsung SmartTV",
                },
            }
        )

        remote.token = "123456789"
        remote_websocket.return_value = remote

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_METHOD] == "websocket"
        assert result["data"][CONF_TOKEN] == "123456789"
        assert result["data"][CONF_MAC] == "gg:ee:tt:mm:aa:cc"
        assert result["data"][CONF_PORT] == 8002
        remote_websocket.assert_called_once_with(**AUTODETECT_WEBSOCKET_SSL)
        rest_api_class.assert_called_once_with(**DEVICEINFO_WEBSOCKET_SSL)
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].data[CONF_MAC] == "gg:ee:tt:mm:aa:cc"