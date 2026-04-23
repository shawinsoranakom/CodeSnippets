def test_detect_radio_hardware(hass: HomeAssistant) -> None:
    """Test logic to detect radio hardware."""
    skyconnect_config_entry = MockConfigEntry(
        data={
            "device": SKYCONNECT_DEVICE,
            "vid": "10C4",
            "pid": "EA60",
            "serial_number": "3c0ed67c628beb11b1cd64a0f320645d",
            "manufacturer": "Nabu Casa",
            "product": "SkyConnect v1.0",
            "firmware": "ezsp",
        },
        version=1,
        minor_version=4,
        domain=SKYCONNECT_DOMAIN,
        options={},
        title="Home Assistant SkyConnect",
    )
    skyconnect_config_entry.add_to_hass(hass)

    connect_zbt1_config_entry = MockConfigEntry(
        data={
            "device": CONNECT_ZBT1_DEVICE,
            "vid": "10C4",
            "pid": "EA60",
            "serial_number": "3c0ed67c628beb11b1cd64a0f320645d",
            "manufacturer": "Nabu Casa",
            "product": "Home Assistant Connect ZBT-1",
            "firmware": "ezsp",
        },
        version=1,
        minor_version=4,
        domain=SKYCONNECT_DOMAIN,
        options={},
        title="Home Assistant Connect ZBT-1",
    )
    connect_zbt1_config_entry.add_to_hass(hass)

    assert _detect_radio_hardware(hass, CONNECT_ZBT1_DEVICE) == HardwareType.SKYCONNECT
    assert _detect_radio_hardware(hass, SKYCONNECT_DEVICE) == HardwareType.SKYCONNECT
    assert (
        _detect_radio_hardware(hass, SKYCONNECT_DEVICE + "_foo") == HardwareType.OTHER
    )
    assert _detect_radio_hardware(hass, "/dev/ttyAMA1") == HardwareType.OTHER

    with patch(
        "homeassistant.components.homeassistant_yellow.hardware.get_os_info",
        return_value={"board": "yellow"},
    ):
        assert _detect_radio_hardware(hass, "/dev/ttyAMA1") == HardwareType.YELLOW
        assert _detect_radio_hardware(hass, "/dev/ttyAMA2") == HardwareType.OTHER
        assert (
            _detect_radio_hardware(hass, SKYCONNECT_DEVICE) == HardwareType.SKYCONNECT
        )