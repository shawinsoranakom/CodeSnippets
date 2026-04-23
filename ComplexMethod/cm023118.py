async def test_parse_qr_code_string(
    hass: HomeAssistant, integration, client, hass_ws_client: WebSocketGenerator
) -> None:
    """Test parse_qr_code_string websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {
        "qrProvisioningInformation": {
            "version": 0,
            "securityClasses": [0],
            "dsk": "test",
            "genericDeviceClass": 1,
            "specificDeviceClass": 1,
            "installerIconType": 1,
            "manufacturerId": 1,
            "productType": 1,
            "productId": 1,
            "applicationVersion": "test",
            "maxInclusionRequestInterval": 1,
            "uuid": "test",
            "supportedProtocols": [0],
        }
    }

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/parse_qr_code_string",
            ENTRY_ID: entry.entry_id,
            QR_CODE_STRING: "90testtesttesttesttesttesttesttesttesttesttesttesttest",
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        VERSION: 0,
        SECURITY_CLASSES: [0],
        DSK: "test",
        GENERIC_DEVICE_CLASS: 1,
        SPECIFIC_DEVICE_CLASS: 1,
        INSTALLER_ICON_TYPE: 1,
        MANUFACTURER_ID: 1,
        PRODUCT_TYPE: 1,
        PRODUCT_ID: 1,
        APPLICATION_VERSION: "test",
        MAX_INCLUSION_REQUEST_INTERVAL: 1,
        UUID: "test",
        SUPPORTED_PROTOCOLS: [Protocols.ZWAVE],
        STATUS: 0,
    }

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "utils.parse_qr_code_string",
        "qr": "90testtesttesttesttesttesttesttesttesttesttesttesttest",
    }

    # Test FailedZWaveCommand is caught
    with patch(
        "homeassistant.components.zwave_js.api.async_parse_qr_code_string",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 6,
                TYPE: "zwave_js/parse_qr_code_string",
                ENTRY_ID: entry.entry_id,
                QR_CODE_STRING: (
                    "90testtesttesttesttesttesttesttesttesttesttesttesttest"
                ),
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
        {
            ID: 7,
            TYPE: "zwave_js/parse_qr_code_string",
            ENTRY_ID: entry.entry_id,
            QR_CODE_STRING: "90testtesttesttesttesttesttesttesttesttesttesttesttest",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED