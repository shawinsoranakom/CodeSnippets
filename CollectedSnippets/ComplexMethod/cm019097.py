async def test_aiousbwatcher_discovery(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that aiousbwatcher can discover a device without raising an exception."""
    new_usb = [{"domain": "test1", "vid": "3039"}, {"domain": "test2", "vid": "0FA0"}]

    mock_ports = [
        USBDevice(
            device=slae_sh_device.device,
            vid="3039",
            pid="3039",
            serial_number=slae_sh_device.serial_number,
            manufacturer=slae_sh_device.manufacturer,
            description=slae_sh_device.description,
        )
    ]

    aiousbwatcher_callback = None

    def async_register_callback(callback):
        nonlocal aiousbwatcher_callback
        aiousbwatcher_callback = callback

    MockAIOUSBWatcher = MagicMock()
    MockAIOUSBWatcher.async_register_callback = async_register_callback

    with (
        patch("sys.platform", "linux"),
        patch("homeassistant.components.usb.async_get_usb", return_value=new_usb),
        patch_scanned_serial_ports(return_value=mock_ports),
        patch(
            "homeassistant.components.usb.AIOUSBWatcher", return_value=MockAIOUSBWatcher
        ),
        patch.object(hass.config_entries.flow, "async_init") as mock_config_flow,
    ):
        assert await async_setup_component(hass, DOMAIN, {"usb": {}})
        await hass.async_block_till_done()
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

        assert aiousbwatcher_callback is not None

        assert len(mock_config_flow.mock_calls) == 1
        assert mock_config_flow.mock_calls[0][1][0] == "test1"
        await hass.async_block_till_done()
        assert len(mock_config_flow.mock_calls) == 1

        mock_ports.append(
            USBDevice(
                device=slae_sh_device.device,
                vid="0FA0",
                pid="0FA0",
                serial_number=slae_sh_device.serial_number,
                manufacturer=slae_sh_device.manufacturer,
                description=slae_sh_device.description,
            )
        )

        aiousbwatcher_callback()
        await hass.async_block_till_done()

        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=usb.ADD_REMOVE_SCAN_COOLDOWN)
        )
        await hass.async_block_till_done(wait_background_tasks=True)

        assert len(mock_config_flow.mock_calls) == 2
        assert mock_config_flow.mock_calls[1][1][0] == "test2"

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        await hass.async_block_till_done()