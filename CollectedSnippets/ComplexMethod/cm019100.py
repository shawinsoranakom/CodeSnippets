async def test_register_port_event_callback_failure(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test port event callback failure handling."""

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

    mock_callback1 = Mock(side_effect=RuntimeError("Failure 1"))
    mock_callback2 = Mock(side_effect=RuntimeError("Failure 2"))

    # Start off with no ports
    with (
        patch_scanned_serial_ports(return_value=[]),
    ):
        assert await async_setup_component(hass, DOMAIN, {"usb": {}})

        usb.async_register_port_event_callback(hass, mock_callback1)
        usb.async_register_port_event_callback(hass, mock_callback2)

    assert mock_callback1.mock_calls == []
    assert mock_callback2.mock_calls == []

    # Add two new ports
    with (
        patch_scanned_serial_ports(return_value=[port1, port2]),
        caplog.at_level(logging.ERROR, logger="homeassistant.components.usb"),
    ):
        await ws_client.send_json({"id": 1, "type": "usb/scan"})
        response = await ws_client.receive_json()
        assert response["success"]
        await hass.async_block_till_done()

    # Both were called even though they raised exceptions
    assert mock_callback1.mock_calls == [call({port1, port2}, set())]
    assert mock_callback2.mock_calls == [call({port1, port2}, set())]

    assert caplog.text.count("Error in USB port event callback") == 2
    assert "Failure 1" in caplog.text
    assert "Failure 2" in caplog.text