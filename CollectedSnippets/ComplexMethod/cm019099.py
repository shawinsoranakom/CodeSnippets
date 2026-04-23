async def test_register_port_event_callback(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test the registration of a port event callback."""

    port1 = USBDevice(
        device=slae_sh_device.device,
        vid="3039",
        pid="3039",
        serial_number=slae_sh_device.serial_number,
        manufacturer=slae_sh_device.manufacturer,
        description=slae_sh_device.description,
    )

    port2 = USBDevice(
        device=conbee_device.device,
        vid="303A",
        pid="303A",
        serial_number=conbee_device.serial_number,
        manufacturer=conbee_device.manufacturer,
        description=conbee_device.description,
    )

    ws_client = await hass_ws_client(hass)

    mock_callback1 = Mock()
    mock_callback2 = Mock()

    # Start off with no ports
    with (
        patch_scanned_serial_ports(return_value=[]),
    ):
        assert await async_setup_component(hass, DOMAIN, {"usb": {}})

        _cancel1 = usb.async_register_port_event_callback(hass, mock_callback1)
        cancel2 = usb.async_register_port_event_callback(hass, mock_callback2)

    assert mock_callback1.mock_calls == []
    assert mock_callback2.mock_calls == []

    # Add two new ports
    with patch_scanned_serial_ports(return_value=[port1, port2]):
        await ws_client.send_json({"id": 1, "type": "usb/scan"})
        response = await ws_client.receive_json()
        assert response["success"]

    assert mock_callback1.mock_calls == [call({port1, port2}, set())]
    assert mock_callback2.mock_calls == [call({port1, port2}, set())]

    # Cancel the second callback
    cancel2()
    cancel2()

    mock_callback1.reset_mock()
    mock_callback2.reset_mock()

    # Remove port 2
    with patch_scanned_serial_ports(return_value=[port1]):
        await ws_client.send_json({"id": 2, "type": "usb/scan"})
        response = await ws_client.receive_json()
        assert response["success"]
        await hass.async_block_till_done()

    assert mock_callback1.mock_calls == [call(set(), {port2})]
    assert mock_callback2.mock_calls == []  # The second callback was unregistered

    mock_callback1.reset_mock()
    mock_callback2.reset_mock()

    # Keep port 2 removed
    with patch_scanned_serial_ports(return_value=[port1]):
        await ws_client.send_json({"id": 3, "type": "usb/scan"})
        response = await ws_client.receive_json()
        assert response["success"]
        await hass.async_block_till_done()

    # Nothing changed so no callback is called
    assert mock_callback1.mock_calls == []
    assert mock_callback2.mock_calls == []

    # Unplug one and plug in the other
    with patch_scanned_serial_ports(return_value=[port2]):
        await ws_client.send_json({"id": 4, "type": "usb/scan"})
        response = await ws_client.receive_json()
        assert response["success"]
        await hass.async_block_till_done()

    assert mock_callback1.mock_calls == [call({port2}, {port1})]
    assert mock_callback2.mock_calls == []