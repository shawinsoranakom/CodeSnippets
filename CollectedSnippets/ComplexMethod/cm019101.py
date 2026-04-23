async def test_removal_aborts_discovery_flows(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test USB device removal aborts the correct discovery flows."""
    # Used by test1
    device1 = USBDevice(
        device="/dev/serial/by-id/unique-device-1",
        vid="1234",
        pid="5678",
        serial_number="ABC123",
        manufacturer="Test Manufacturer 1",
        description="Test Device 1 for domain test1",
    )

    # Used by test1
    device2 = USBDevice(
        device="/dev/serial/by-id/unique-device-2",
        vid="ABCD",
        pid="EF01",
        serial_number="XYZ789",
        manufacturer="Test Manufacturer 2",
        description="Test Device 2 for domain test1",
    )

    # Used by test2
    device3 = USBDevice(
        device="/dev/serial/by-id/unique-device-3",
        vid="AAAA",
        pid="BBBB",
        serial_number="ABCDEF",
        manufacturer="Test Manufacturer 3",
        description="Test Device 3 for domain test2",
    )

    # Not used by any domain
    device4 = USBDevice(
        device="/dev/serial/by-id/unique-device-4",
        vid="CCCC",
        pid="DDDD",
        serial_number="ABCDEF",
        manufacturer="Test Manufacturer 4",
        description="Test Device 4",
    )

    # Used by both test1 and test2
    device5 = USBDevice(
        device="/dev/serial/by-id/multi-domain-device",
        vid="FFFF",
        pid="EEEE",
        serial_number="MULTI123",
        manufacturer="Test Manufacturer 5",
        description="Device matching multiple domains",
    )

    class TestFlow(config_entries.ConfigFlow):
        VERSION = 1

        async def async_step_usb(self, discovery_info):
            return self.async_show_form(step_id="confirm")

        async def async_step_confirm(self, user_input=None):
            # There's no way to exit
            return self.async_show_form(step_id="confirm")

    mock_integration(hass, MockModule("test1"))
    mock_platform(hass, "test1.config_flow", None)

    mock_integration(hass, MockModule("test2"))
    mock_platform(hass, "test2.config_flow", None)

    ws_client = await hass_ws_client(hass)

    with (
        patch(
            "homeassistant.components.usb.async_get_usb",
            return_value=[
                # Domain `test1` matches devices 1 and 2
                {"domain": "test1", "vid": "1234", "pid": "5678"},
                {"domain": "test1", "vid": "ABCD", "pid": "EF01"},
                # Domain `test2` matches device 3
                {"domain": "test2", "vid": "AAAA", "pid": "BBBB"},
                # Both domains match device 5
                {"domain": "test1", "vid": "FFFF", "pid": "EEEE"},
                {"domain": "test2", "vid": "FFFF", "pid": "EEEE"},
            ],
        ),
        # All devices are plugged in initially
        patch_scanned_serial_ports(
            return_value=[device1, device2, device3, device4, device5]
        ),
        mock_config_flow("test1", TestFlow),
        mock_config_flow("test2", TestFlow),
    ):
        assert await async_setup_component(hass, DOMAIN, {"usb": {}})
        await hass.async_block_till_done()
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

        # Discovery will create five flows (device5 is matched by both domains)
        flows = hass.config_entries.flow.async_progress()
        assert len(flows) == 5

        # Three flows for test1 (1, 2, 5), two for test2 (3, 5)
        assert sorted([flow["handler"] for flow in flows]) == [
            "test1",
            "test1",
            "test1",
            "test2",
            "test2",
        ]

        # Device 5 is removed
        with patch_scanned_serial_ports(
            return_value=[device1, device2, device3, device4]
        ):
            await ws_client.send_json({"id": 1, "type": "usb/scan"})
            response = await ws_client.receive_json()
            assert response["success"]
            await hass.async_block_till_done()

        # Both flows for device5 should be aborted (one test1, one test2)
        remaining_flows = hass.config_entries.flow.async_progress()
        assert len(remaining_flows) == 3
        assert sorted([flow["handler"] for flow in remaining_flows]) == [
            "test1",
            "test1",
            "test2",
        ]

        # Device 3 disappears
        with patch_scanned_serial_ports(return_value=[device1, device2, device4]):
            await ws_client.send_json({"id": 2, "type": "usb/scan"})
            response = await ws_client.receive_json()
            assert response["success"]
            await hass.async_block_till_done()

        # The corresponding flow is removed
        remaining_flows = hass.config_entries.flow.async_progress()
        assert len(remaining_flows) == 2
        assert sorted([flow["handler"] for flow in remaining_flows]) == [
            "test1",
            "test1",
        ]

        # Remove the others
        with patch_scanned_serial_ports(return_value=[]):
            await ws_client.send_json({"id": 3, "type": "usb/scan"})
            response = await ws_client.receive_json()
            assert response["success"]
            await hass.async_block_till_done()

        # All the remaining flows should be aborted
        assert len(hass.config_entries.flow.async_progress()) == 0

        # Plug one back in and the unused device4
        with patch_scanned_serial_ports(return_value=[device3, device4]):
            await ws_client.send_json({"id": 4, "type": "usb/scan"})
            response = await ws_client.receive_json()
            assert response["success"]
            await hass.async_block_till_done()

        # A new flow is re-created for the old device
        final_flows = hass.config_entries.flow.async_progress()
        assert len(final_flows) == 1
        assert final_flows[0]["handler"] == "test2"