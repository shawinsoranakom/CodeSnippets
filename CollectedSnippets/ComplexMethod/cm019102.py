async def test_list_serial_ports(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    setup_usb: MagicMock,
) -> None:
    """Test listing serial ports via websocket."""
    setup_usb.return_value = [
        USBDevice(
            device="/dev/ttyUSB0",
            vid="10C4",
            pid="EA60",
            serial_number="001234",
            manufacturer="Silicon Labs",
            description="CP2102 USB to UART",
        ),
        SerialDevice(
            device="/dev/ttyS0",
            serial_number=None,
            manufacturer=None,
            description="ttyS0",
        ),
    ]

    ws_client = await hass_ws_client(hass)
    await ws_client.send_json({"id": 1, "type": "usb/list_serial_ports"})
    response = await ws_client.receive_json()

    assert response["success"]
    result = response["result"]
    assert len(result) == 2

    assert result[0]["device"] == "/dev/ttyUSB0"
    assert result[0]["vid"] == "10C4"
    assert result[0]["pid"] == "EA60"
    assert result[0]["serial_number"] == "001234"
    assert result[0]["manufacturer"] == "Silicon Labs"
    assert result[0]["description"] == "CP2102 USB to UART"

    assert result[1]["device"] == "/dev/ttyS0"
    assert result[1]["serial_number"] is None
    assert result[1]["manufacturer"] is None
    assert result[1]["description"] == "ttyS0"
    assert "vid" not in result[1]
    assert "pid" not in result[1]