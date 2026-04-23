async def test_try_parse_dsk_from_qr_code_string(
    hass: HomeAssistant, integration, client, hass_ws_client: WebSocketGenerator
) -> None:
    """Test try_parse_dsk_from_qr_code_string websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {"dsk": "a"}

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/try_parse_dsk_from_qr_code_string",
            ENTRY_ID: entry.entry_id,
            QR_CODE_STRING: "90testtesttesttesttesttesttesttesttesttesttesttesttest",
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"] == "a"

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "utils.try_parse_dsk_from_qr_code_string",
        "qr": "90testtesttesttesttesttesttesttesttesttesttesttesttest",
    }

    # Test FailedZWaveCommand is caught
    with patch(
        "homeassistant.components.zwave_js.api.async_try_parse_dsk_from_qr_code_string",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 6,
                TYPE: "zwave_js/try_parse_dsk_from_qr_code_string",
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
            TYPE: "zwave_js/try_parse_dsk_from_qr_code_string",
            ENTRY_ID: entry.entry_id,
            QR_CODE_STRING: "90testtesttesttesttesttesttesttesttesttesttesttesttest",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED