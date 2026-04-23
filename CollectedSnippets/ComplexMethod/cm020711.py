async def test_list_serial_ports_ignored_devices(hass: HomeAssistant) -> None:
    """Test that list_serial_ports filters out ignored non-Zigbee devices."""
    mock_ports = [
        USBDevice(
            device="/dev/ttyUSB0",
            vid="303A",
            pid="4001",
            serial_number="1234",
            manufacturer="Nabu Casa",
            description="ZWA-2",
        ),
        USBDevice(
            device="/dev/ttyUSB1",
            vid="303A",
            pid="4001",
            serial_number="1235",
            manufacturer="Nabu Casa",
            description="ZBT-2",
        ),
        USBDevice(
            device="/dev/ttyUSB2",
            vid="10C4",
            pid="EA60",
            serial_number="1236",
            manufacturer="Nabu Casa",
            description="Home Assistant Connect ZBT-1",
        ),
        USBDevice(
            device="/dev/ttyUSB3",
            vid="10C4",
            pid="EA60",
            serial_number="1237",
            manufacturer="Nabu Casa",
            description="SkyConnect v1.0",
        ),
        USBDevice(
            device="/dev/ttyUSB4",
            vid="1234",
            pid="5678",
            serial_number="1238",
            manufacturer="Another Manufacturer",
            description="Zigbee USB Adapter",
        ),
        USBDevice(
            device="/dev/ttyUSB5",
            vid="1234",
            pid="5678",
            serial_number=None,
            manufacturer=None,
            description=None,
        ),
    ]

    with (
        patch("homeassistant.components.zha.config_flow.is_hassio", return_value=False),
        patch(
            "homeassistant.components.zha.config_flow.async_scan_serial_ports",
            return_value=mock_ports,
        ),
    ):
        ports = await config_flow.list_serial_ports(hass)

    # ZWA-2 should be filtered out, others should remain
    assert len(ports) == 5

    assert ports[0].device == "/dev/ttyUSB1"
    assert ports[0].manufacturer == "Nabu Casa"
    assert ports[0].description == "ZBT-2"

    assert ports[1].device == "/dev/ttyUSB2"
    assert ports[1].manufacturer == "Nabu Casa"
    assert ports[1].description == "Home Assistant Connect ZBT-1"

    assert ports[2].device == "/dev/ttyUSB3"
    assert ports[2].manufacturer == "Nabu Casa"
    assert ports[2].description == "SkyConnect v1.0"

    assert ports[3].device == "/dev/ttyUSB4"
    assert ports[3].manufacturer == "Another Manufacturer"
    assert ports[3].description == "Zigbee USB Adapter"

    assert ports[4].device == "/dev/ttyUSB5"
    assert ports[4].manufacturer is None
    assert ports[4].description is None